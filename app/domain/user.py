from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserContext:
    user_id: str
    roles: tuple[str, ...]

    def has_role(self, role: str) -> bool:
        return role in self.roles
