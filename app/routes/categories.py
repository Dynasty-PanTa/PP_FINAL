from flask import request
from flask_restx import Namespace, Resource, fields
from ..models import Category
from ..extensions import db
from ..schemas import CategorySchema

cat_ns = Namespace('categories', description='Category operations')
cat_model = cat_ns.model('Category', {'name': fields.String(required=True), 'description': fields.String()})

@cat_ns.route('')
class CategoryList(Resource):
    def get(self):
        cats = Category.query.all()
        return CategorySchema(many=True).dump(cats), 200

    @cat_ns.expect(cat_model)
    def post(self):
        data = request.get_json()
        if Category.query.filter_by(name=data['name']).first():
            return {'message':'Category exists'}, 400
        cat = Category(name=data['name'], description=data.get('description'))
        db.session.add(cat)
        db.session.commit()
        return CategorySchema().dump(cat), 201

@cat_ns.route('/<int:id>')
class CategoryItem(Resource):
    def get(self, id):
        c = Category.query.get_or_404(id)
        return CategorySchema().dump(c), 200

    @cat_ns.expect(cat_model)
    def put(self, id):
        c = Category.query.get_or_404(id)
        data = request.get_json()
        c.name = data.get('name', c.name)
        c.description = data.get('description', c.description)
        db.session.commit()
        return CategorySchema().dump(c), 200

    def delete(self, id):
        c = Category.query.get_or_404(id)
        db.session.delete(c)
        db.session.commit()
        return {'message':'Deleted'}, 200
