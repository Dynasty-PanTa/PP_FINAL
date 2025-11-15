import os
from flask import request, current_app, url_for
from flask_restx import Namespace, Resource, fields
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import Product, Category

prod_ns = Namespace("products", description="Product operations", security="Bearer Auth")

# Swagger model for non-file fields
prod_model = prod_ns.model("Product", {
    "name": fields.String(required=True),
    "description": fields.String(),
    "price": fields.Float(required=True),
    "quantity": fields.Integer(required=True),
    "category_id": fields.Integer(required=True)
})

# Parser for file uploads
upload_parser = prod_ns.parser()
upload_parser.add_argument("name", type=str, required=True, location="form")
upload_parser.add_argument("description", type=str, required=False, location="form")
upload_parser.add_argument("price", type=float, required=True, location="form")
upload_parser.add_argument("quantity", type=int, required=True, location="form")
upload_parser.add_argument("category_id", type=int, required=True, location="form")
upload_parser.add_argument("image", type="file", location="files")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


@prod_ns.route("")
class ProductList(Resource):

    @jwt_required()
    def get(self):
        products = Product.query.all()
        result = []

        for p in products:
            result.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price_cents / 100.0,
                "quantity": p.quantity,
                "category_id": p.category_id,
                "image_url": url_for("uploaded_file", filename=p.image_filename, _external=True) if p.image_filename else None
            })

        return result, 200

    @jwt_required()
    @prod_ns.expect(upload_parser)
    def post(self):
        data = request.form
        try:
            name = data.get("name")
            description = data.get("description")
            price = float(data.get("price"))
            quantity = int(data.get("quantity"))
            category_id = int(data.get("category_id"))

            if not Category.query.get(category_id):
                return {"message": "Invalid category_id"}, 400

            image_file = request.files.get("image")
            image_filename = None

            if image_file:
                if image_file.filename == "":
                    return {"message": "No selected image"}, 400
                if not allowed_file(image_file.filename):
                    return {"message": "Invalid image type"}, 400

                image_filename = secure_filename(image_file.filename)
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], image_filename)
                image_file.save(save_path)

            new_product = Product(
                name=name,
                description=description,
                price_cents=int(price * 100),
                quantity=quantity,
                category_id=category_id,
                image_filename=image_filename
            )

            db.session.add(new_product)
            db.session.commit()
            return {"message": "Product created", "id": new_product.id}, 201

        except Exception as e:
            db.session.rollback()
            return {"message": f"Internal Server Error: {str(e)}"}, 500


@prod_ns.route("/<int:id>")
class ProductItem(Resource):

    @jwt_required()
    def get(self, id):
        p = Product.query.get_or_404(id)
        return {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price_cents / 100.0,
            "quantity": p.quantity,
            "category_id": p.category_id,
            "image_url": url_for("uploaded_file", filename=p.image_filename, _external=True) if p.image_filename else None
        }, 200

    @jwt_required()
    @prod_ns.expect(upload_parser)
    def put(self, id):
        p = Product.query.get_or_404(id)
        data = request.form
        try:
            p.name = data.get("name", p.name)
            p.description = data.get("description", p.description)

            if data.get("price"):
                p.price_cents = int(float(data.get("price")) * 100)

            if data.get("quantity"):
                p.quantity = int(data.get("quantity"))

            if data.get("category_id"):
                category_id = int(data.get("category_id"))
                if not Category.query.get(category_id):
                    return {"message": "Invalid category_id"}, 400
                p.category_id = category_id

            image_file = request.files.get("image")
            if image_file:
                if not allowed_file(image_file.filename):
                    return {"message": "Invalid image type"}, 400
                filename = secure_filename(image_file.filename)
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                image_file.save(save_path)
                p.image_filename = filename

            db.session.commit()
            return {"message": "Product updated"}, 200

        except Exception as e:
            db.session.rollback()
            return {"message": f"Internal Server Error: {str(e)}"}, 500

    @jwt_required()
    def delete(self, id):
        p = Product.query.get_or_404(id)
        try:
            if p.image_filename:
                file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], p.image_filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

            db.session.delete(p)
            db.session.commit()
            return {"message": "Product deleted"}, 200

        except Exception as e:
            db.session.rollback()
            return {"message": f"Internal Server Error: {str(e)}"}, 500
