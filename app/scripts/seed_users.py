from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.enums.role import UserRole
from app.repositories.user_repository import UserRepository


def upsert_user(
    *,
    username: str,
    email: str,
    password: str,
    role: UserRole,
) -> None:
    with SessionLocal() as db:
        repository = UserRepository(db)
        user = repository.get_by_username(username)

        if user is None:
            repository.create(
                username=username,
                email=email,
                password_hash=hash_password(password),
                role=role,
                is_active=True,
            )
            print(f"[created] {role.value}: {username}")
            return

        user.email = email
        user.password_hash = hash_password(password)
        user.role = role
        user.is_active = True
        repository.save(user)
        print(f"[updated] {role.value}: {username}")


def main() -> None:
    upsert_user(
        username=settings.seed_admin_username,
        email=settings.seed_admin_email,
        password=settings.seed_admin_password,
        role=UserRole.ADMIN,
    )

    upsert_user(
        username=settings.seed_user_username,
        email=settings.seed_user_email,
        password=settings.seed_user_password,
        role=UserRole.USER,
    )

    print("Seed de usuários concluída.")


if __name__ == "__main__":
    main()
