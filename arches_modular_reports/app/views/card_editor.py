from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)

from arches_querysets.rest_framework.permissions import Guest
from arches_querysets.rest_framework.serializers import (
    ArchesResourceSerializer,
    ArchesTileSerializer,
)
from arches_querysets.rest_framework.view_mixins import ArchesModelAPIMixin


# class ModularReportResourceDetailView(ArchesModelAPIMixin, RetrieveUpdateDestroyAPIView):
#     permission_classes = [Guest]
#     serializer_class = ArchesResourceSerializer


# class ModularReportTileListCreateView(ArchesModelAPIMixin, ListCreateAPIView):
#     permission_classes = [Guest]
#     serializer_class = ArchesTileSerializer


class ModularReportTileDetailView(ArchesModelAPIMixin, RetrieveAPIView):
    permission_classes = [Guest]
    serializer_class = ArchesTileSerializer
