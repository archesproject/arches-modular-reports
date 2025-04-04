from rest_framework import renderers
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from arches_querysets.rest_framework.permissions import Guest
from arches_querysets.rest_framework.serializers import (
    ArchesResourceSerializer,
    ArchesTileSerializer,
)
from arches_querysets.rest_framework.view_mixins import ArchesModelAPIMixin


class ProvenanceResourceDetailView(ArchesModelAPIMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = [Guest]
    renderer_classes = [renderers.JSONRenderer]
    serializer_class = ArchesResourceSerializer


class ProvenanceTileListCreateView(ArchesModelAPIMixin, ListCreateAPIView):
    permission_classes = [Guest]
    renderer_classes = [renderers.JSONRenderer]
    serializer_class = ArchesTileSerializer


class ProvenanceTileDetailView(ArchesModelAPIMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = [Guest]
    renderer_classes = [renderers.JSONRenderer]
    serializer_class = ArchesTileSerializer
