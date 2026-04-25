from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.roles.role_router import RoleCreateSchema

def create_role_service(
    db: Session,
    role_data: RoleCreateSchema
):
   
    existing_role = db.execute(
        "SELECT id FROM roles WHERE name = :name",
        {"name": role_data.name}
    ).fetchone()

    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already exists"
        )

   
    result = db.execute(
        "INSERT INTO roles (name, description) VALUES (:name, :desc) RETURNING id",
        {
            "name": role_data.name,
            "desc": role_data.description
        }
    )
    role_id = result.fetchone()[0]

   
    for module, perms in role_data.permissions.items():
        db.execute(
            """
            INSERT INTO role_permissions
            (role_id, module, can_read, can_write, can_delete)
            VALUES (:rid, :module, :r, :w, :d)
            """,
            {
                "rid": role_id,
                "module": module,
                "r": perms.read,
                "w": perms.write,
                "d": perms.delete
            }
        )

    db.commit()

    return {
        "id": role_id,
        "name": role_data.name,
        "description": role_data.description
    }


def list_roles_service(db: Session):
    roles = db.execute("SELECT id, name, description FROM roles").fetchall()

    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description
        }
        for r in roles
    ]
