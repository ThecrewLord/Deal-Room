from app import create_app
from app.database import db
from app.models.system.tag import Tag

app = create_app()

with app.app_context():
    tags = [
        ("Decision Maker", "Decision Maker"),
        ("Technical Champion", "Technical Champion"),
        ("End User", "End User"),
        ("Blocker", "Blocker"),
    ]

    for name, color in tags:
        existing = Tag.query.filter_by(name=name).first()
        if not existing:
            db.session.add(Tag(
                name=name,
                color=color,
                is_active=True,
            ))

    db.session.commit()

    print("V2 tags:")
    for tag in Tag.query.order_by(Tag.tag_id).all():
        print(tag.tag_id, tag.name, tag.is_active)
