from __future__ import annotations

from drf_spectacular.openapi import AutoSchema


class AppTagsAutoSchema(AutoSchema):
    """
    Group Swagger operations by Django app.

    - Respects explicit tags set via @extend_schema(tags=[...]).
    - Otherwise derives a tag from the view's module (e.g. "users.api" -> "Users").
    """

    _APP_TAGS = {
        "users": "Users",
        "academics": "Academics",
        "finance": "Finance",
        "core": "Core",
    }

    def get_tags(self) -> list[str]:
        # If a view explicitly sets tags via drf-spectacular overrides, keep them.
        tags = super().get_tags()
        if tags:
            # drf-spectacular defaults to ["api"] in many setups; treat that as "unset".
            if not (len(tags) == 1 and tags[0] in {"api", "default"}):
                return tags

        view_cls = self.view.__class__
        module = getattr(view_cls, "__module__", "") or ""
        app = module.split(".", 1)[0] if module else ""

        if app in self._APP_TAGS:
            return [self._APP_TAGS[app]]

        # Fall back to previous behavior.
        return tags or ["api"]

