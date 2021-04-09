from rest_framework.renderers import JSONRenderer


class CustomJsonRenderer(JSONRenderer):
    charset = "utf-8"
