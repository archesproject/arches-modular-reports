import uuid

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
)


def make_graph(slug):
    Graph.objects.create_graph(is_resource=True, slug=slug)
    Graph.objects.filter(slug=slug).exclude(source_identifier=None).delete()
    return Graph.objects.get(slug=slug)


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

    def test_report_context(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("api_report_context", args=[self.resource.pk])
        )
        self.assertEqual(response.status_code, 200)
        context = response.json()
        self.assertEqual(context["graph"]["slug"], "endpoint_graph")
        self.assertIn("name", context["lifecycle_state"])
        self.assertTrue(context["permissions"]["can_edit"])

    def test_edit_history_describes_values_without_email(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("api_edit_history", args=[self.resource.pk]))
        self.assertEqual(response.status_code, 200)
        history = response.json()
        self.assertEqual(history["total_count"], 1)
        edit = history["results"][0]
        self.assertEqual(edit["user"], "Ada Lovelace")
        self.assertEqual(edit["card_name"], "Names")
        self.assertNotIn("ada@example.com", response.content.decode())
        name_value = [
            value for value in edit["values"] if value["node_alias"] == "name_content"
        ][0]
        self.assertEqual(name_value["before"], "Old")
        self.assertEqual(name_value["after"], "New")
        self.assertTrue(name_value["changed"])

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

    def test_related_resource_groups(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("api_related_resource_groups", args=[self.resource.pk])
        )
        self.assertEqual(response.status_code, 200)
        groups = response.json()["groups"]
        self.assertEqual([group["graph_slug"] for group in groups], ["related_graph"])
        self.assertEqual(groups[0]["total_count"], 1)
        self.assertEqual(
            groups[0]["items"][0]["report_url"],
            reverse("resource_report", args=[self.related_resource.pk]),
        )

        single_group_response = self.client.get(
            reverse("api_related_resource_groups", args=[self.resource.pk]),
            {"graph": "related_graph", "page": 1},
        )
        self.assertEqual(single_group_response.json()["graph_slug"], "related_graph")

    def test_node_presentation_includes_schema_fields(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("api_node_presentation", args=[self.resource.pk])
        )
        self.assertEqual(response.status_code, 200)
        name_content = response.json()["name_content"]
        self.assertEqual(name_content["datatype"], "string")
        self.assertEqual(name_content["nodegroup"]["alias"], "names")
        self.assertIsNone(name_content["nodegroup"]["parent_nodegroup_id"])
        self.assertTrue(name_content["nodegroup"]["writable"])
