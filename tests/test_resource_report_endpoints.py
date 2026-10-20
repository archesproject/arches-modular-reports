import uuid
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from guardian.shortcuts import assign_perm

from arches.app.models.graph import Graph
from arches.app.models.models import (
    CardModel,
    EditLog,
    Node,
    NodeGroup,
    ResourceInstance,
    ResourceXResource,
    TileModel,
)


def make_graph(slug):
    Graph.objects.create_graph(is_resource=True, slug=slug)
    Graph.objects.filter(slug=slug).exclude(source_identifier=None).delete()
    return Graph.objects.get(slug=slug)


def make_nodegroup(graph, alias):
    nodegroup = NodeGroup.objects.create(cardinality="n")
    Node.objects.create(
        pk=nodegroup.pk,
        name=alias.title(),
        alias=alias,
        graph=graph,
        nodegroup=nodegroup,
        datatype="semantic",
        istopnode=False,
    )
    return nodegroup


class ResourceReportEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.graph = make_graph("endpoint_graph")
        cls.related_graph = make_graph("related_graph")

        cls.names = NodeGroup.objects.create(cardinality="n")
        grouping_node = Node.objects.create(
            pk=cls.names.pk,
            name="Names",
            alias="names",
            graph=cls.graph,
            nodegroup=cls.names,
            datatype="semantic",
            istopnode=False,
        )
        cls.names.grouping_node = grouping_node
        cls.names.save()
        cls.name_content = Node.objects.create(
            nodegroup=cls.names,
            name="Name content",
            alias="name_content",
            graph=cls.graph,
            istopnode=False,
            datatype="string",
        )
        cls.related_thing = Node.objects.create(
            nodegroup=cls.names,
            name="Related thing",
            alias="related_thing",
            graph=cls.graph,
            istopnode=False,
            datatype="resource-instance",
        )
        CardModel.objects.create(
            graph=cls.graph, nodegroup=cls.names, name="Names", visible=True
        )

        cls.resource = ResourceInstance.objects.create(graph=cls.graph)
        cls.related_resource = ResourceInstance.objects.create(graph=cls.related_graph)
        ResourceXResource.objects.create(
            from_resource=cls.resource,
            from_resource_graph=cls.graph,
            to_resource=cls.related_resource,
            to_resource_graph=cls.related_graph,
            node=cls.related_thing,
        )

        EditLog.objects.create(
            resourceinstanceid=str(cls.resource.pk),
            nodegroupid=str(cls.names.pk),
            tileinstanceid=str(uuid.uuid4()),
            edittype="tile edit",
            oldvalue={
                str(cls.name_content.pk): {"en": {"value": "Old", "direction": "ltr"}}
            },
            newvalue={
                str(cls.name_content.pk): {"en": {"value": "New", "direction": "ltr"}}
            },
            timestamp=timezone.now(),
            user_username="ada",
            user_firstname="Ada",
            user_lastname="Lovelace",
            user_email="ada@example.com",
        )

        cls.superuser = User.objects.create_superuser("report_admin", "", "password")
        cls.reader_user = User.objects.create_user("report_reader", "", "password")

    def test_edit_history_describes_values_without_email(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("api_edit_history", args=[self.resource.pk]))
        self.assertEqual(response.status_code, 200)
        edit = response.json()["results"][0]
        self.assertEqual(edit["user"], "Ada Lovelace")
        self.assertNotIn("ada@example.com", response.content.decode())
        name_value = [
            value for value in edit["values"] if value["node_alias"] == "name_content"
        ][0]
        self.assertEqual(name_value["before"], "Old")
        self.assertEqual(name_value["after"], "New")

    def test_edit_history_filters_by_user_and_card_name(self):
        EditLog.objects.create(
            resourceinstanceid=str(self.resource.pk),
            edittype="create",
            timestamp=timezone.now(),
            user_username="grace",
            user_firstname="Grace",
            user_lastname="Hopper",
        )
        self.client.force_login(self.superuser)
        history_url = reverse("api_edit_history", args=[self.resource.pk])

        def matching_users(query):
            response = self.client.get(history_url, {"q": query})
            return [edit["user"] for edit in response.json()["results"]]

        self.assertEqual(matching_users("lovelace"), ["Ada Lovelace"])
        self.assertEqual(matching_users("NAMES"), ["Ada Lovelace"])

    def test_related_resource_groups_for_listed_models_and_query(self):
        ResourceInstance.objects.filter(pk=self.related_resource.pk).update(
            name={"en": "Smalt sample"}
        )
        self.client.force_login(self.superuser)
        groups_url = reverse("api_related_resource_groups", args=[self.resource.pk])

        listed_groups = self.client.get(
            groups_url, {"graphs": "related_graph,endpoint_graph"}
        ).json()["groups"]
        self.assertEqual(
            [group["graph_slug"] for group in listed_groups],
            ["related_graph", "endpoint_graph"],
        )
        self.assertEqual([group["total_count"] for group in listed_groups], [1, 0])

        def related_count(query):
            groups = self.client.get(
                groups_url, {"graphs": "related_graph", "q": query}
            ).json()["groups"]
            return groups[0]["total_count"]

        self.assertEqual(related_count("smalt"), 1)
        self.assertEqual(related_count("nothing"), 0)

    def add_related_photos(self):
        photos = NodeGroup.objects.create(cardinality="n")
        Node.objects.create(
            pk=photos.pk,
            name="Photos",
            alias="photos",
            graph=self.related_graph,
            nodegroup=photos,
            datatype="semantic",
            istopnode=False,
        )
        photo_files = Node.objects.create(
            nodegroup=photos,
            name="Photo files",
            alias="photo_files",
            graph=self.related_graph,
            istopnode=False,
            datatype="file-list",
        )
        ResourceInstance.objects.filter(pk=self.related_resource.pk).update(
            name={"en": "Pyrite photo set"}
        )
        TileModel.objects.create(
            resourceinstance=self.related_resource,
            nodegroup=photos,
            data={
                str(photo_files.pk): [
                    {
                        "name": "pyrite_1.jpg",
                        "url": "/files/pyrite_1",
                        "type": "image/jpeg",
                        "title": {"en": {"value": "Front view", "direction": "ltr"}},
                        "altText": {"en": {"value": "A cube", "direction": "ltr"}},
                    },
                    {
                        "name": "spectrum.pdf",
                        "url": "/files/spectrum",
                        "type": "application/pdf",
                    },
                ]
            },
        )
        return photos

    def test_resource_images_come_from_related_file_nodes(self):
        self.add_related_photos()
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse("api_resource_images", args=[self.resource.pk]),
            {"sources": "related_graph:photo_files"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["images"],
            [
                {
                    "url": "/files/pyrite_1",
                    "caption": "Front view",
                    "alt_text": "A cube",
                    "resourceinstanceid": str(self.related_resource.pk),
                    "resource_name": "Pyrite photo set",
                    "report_url": reverse(
                        "resource_report", args=[self.related_resource.pk]
                    ),
                }
            ],
        )

    def test_resource_images_skip_relationships_the_user_cannot_read(self):
        self.add_related_photos()
        make_nodegroup(self.graph, "notes")
        assign_perm("models.view_resourceinstance", self.reader_user, self.resource)
        assign_perm(
            "models.view_resourceinstance", self.reader_user, self.related_resource
        )
        self.client.force_login(self.reader_user)

        def image_count():
            response = self.client.get(
                reverse("api_resource_images", args=[self.resource.pk]),
                {"sources": "related_graph:photo_files"},
            )
            return len(response.json()["images"])

        self.assertEqual(image_count(), 1)
        assign_perm("models.no_access_to_nodegroup", self.reader_user, self.names)
        self.assertEqual(image_count(), 0)

    def test_dangling_relations_do_not_break_related_resources_or_images(self):
        self.add_related_photos()
        ResourceXResource.objects.create(
            from_resource=self.resource,
            from_resource_graph=self.graph,
            to_resource_id=uuid.uuid4(),
            to_resource_graph=self.related_graph,
            node=self.related_thing,
        )
        assign_perm("models.view_resourceinstance", self.reader_user, self.resource)
        assign_perm(
            "models.view_resourceinstance", self.reader_user, self.related_resource
        )
        self.client.force_login(self.reader_user)

        groups_response = self.client.get(
            reverse("api_related_resource_groups", args=[self.resource.pk]),
            {"graphs": "related_graph"},
        )
        images_response = self.client.get(
            reverse("api_resource_images", args=[self.resource.pk]),
            {"sources": "related_graph:photo_files"},
        )

        self.assertEqual(groups_response.json()["groups"][0]["total_count"], 1)
        self.assertEqual(len(images_response.json()["images"]), 1)

    def test_edit_history_hides_unreadable_nodegroups(self):
        self.client.force_login(self.superuser)

        with mock.patch(
            "arches_modular_reports.app.views.modular_report.get_nodegroups_by_perm",
            return_value=[],
        ):
            response = self.client.get(
                reverse("api_edit_history", args=[self.resource.pk])
            )

        self.assertEqual(response.json()["total_count"], 0)

    def test_resource_images_skip_unreadable_file_nodegroups(self):
        photos = self.add_related_photos()
        make_nodegroup(self.graph, "notes")
        assign_perm("models.view_resourceinstance", self.reader_user, self.resource)
        assign_perm(
            "models.view_resourceinstance", self.reader_user, self.related_resource
        )
        assign_perm("models.no_access_to_nodegroup", self.reader_user, photos)
        self.client.force_login(self.reader_user)

        response = self.client.get(
            reverse("api_resource_images", args=[self.resource.pk]),
            {"sources": "related_graph:photo_files"},
        )

        self.assertEqual(response.json()["images"], [])

    def test_resource_images_skip_related_resources_the_user_cannot_read(self):
        self.add_related_photos()
        make_nodegroup(self.graph, "notes")
        assign_perm("models.view_resourceinstance", self.reader_user, self.resource)
        self.client.force_login(self.reader_user)

        response = self.client.get(
            reverse("api_resource_images", args=[self.resource.pk]),
            {"sources": "related_graph:photo_files"},
        )

        self.assertEqual(response.json()["images"], [])

    def test_related_resource_groups_count_only_what_the_user_can_read(self):
        make_nodegroup(self.related_graph, "details")
        hidden_resource = ResourceInstance.objects.create(graph=self.related_graph)
        ResourceXResource.objects.create(
            from_resource=self.resource,
            from_resource_graph=self.graph,
            to_resource=hidden_resource,
            to_resource_graph=self.related_graph,
            node=self.related_thing,
        )
        secrets = make_nodegroup(self.graph, "secrets")
        ResourceXResource.objects.create(
            from_resource=self.resource,
            from_resource_graph=self.graph,
            to_resource=self.related_resource,
            to_resource_graph=self.related_graph,
            node=Node.objects.create(
                nodegroup=secrets,
                name="Secret link",
                alias="secret_link",
                graph=self.graph,
                istopnode=False,
                datatype="resource-instance",
            ),
        )
        assign_perm("models.view_resourceinstance", self.reader_user, self.resource)
        assign_perm(
            "models.view_resourceinstance", self.reader_user, self.related_resource
        )
        assign_perm("models.no_access_to_nodegroup", self.reader_user, secrets)
        self.client.force_login(self.reader_user)

        [group] = self.client.get(
            reverse("api_related_resource_groups", args=[self.resource.pk]),
            {"graphs": "related_graph"},
        ).json()["groups"]

        self.assertEqual(group["total_count"], 1)
        self.assertEqual(
            [item["report_url"] for item in group["items"]],
            [reverse("resource_report", args=[self.related_resource.pk])],
        )

    def test_reader_without_edit_permission(self):
        assign_perm("models.view_resourceinstance", self.reader_user, self.resource)
        assign_perm("models.read_nodegroup", self.reader_user, self.names)
        self.client.force_login(self.reader_user)

        context_response = self.client.get(
            reverse("api_report_context", args=[self.resource.pk])
        )
        self.assertEqual(context_response.status_code, 200)
        self.assertFalse(context_response.json()["permissions"]["can_edit"])

        history_response = self.client.get(
            reverse("api_edit_history", args=[self.resource.pk])
        )
        self.assertEqual(history_response.status_code, 403)

    def test_related_resource_group_pages_one_model(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("api_related_resource_groups", args=[self.resource.pk]),
            {"graph": "related_graph", "page": 1},
        )
        self.assertEqual(response.json()["graph_slug"], "related_graph")
