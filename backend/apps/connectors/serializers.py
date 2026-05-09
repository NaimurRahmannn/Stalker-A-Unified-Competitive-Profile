from rest_framework import serializers


class ConnectorHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
