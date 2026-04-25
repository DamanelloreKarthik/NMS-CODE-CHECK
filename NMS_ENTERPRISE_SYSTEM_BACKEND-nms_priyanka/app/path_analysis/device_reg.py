from sqlalchemy.orm import Session
from app.path_analysis.models import Device, DeviceCredential
from app.path_analysis.utils.security import encrypt_password


def register_device(db: Session, device_data):

    # ------------------------------------------------
    # 1️⃣ Create Device
    # ------------------------------------------------

    new_device = Device(
        name=device_data.name,
        ip_address=device_data.ip_address,
        category=device_data.category
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    # ------------------------------------------------
    # 2️⃣ Encrypt Password Automatically
    # ------------------------------------------------

    encrypted_password = encrypt_password(device_data.password)

    credential = DeviceCredential(
        device_id=new_device.id,
        username=device_data.username,
        encrypted_password=encrypted_password,
        is_primary=True
    )

    db.add(credential)
    db.commit()

    return new_device