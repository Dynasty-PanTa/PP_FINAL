from marshmallow import Schema, fields

class CategorySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str()

class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str()
    price = fields.Float(required=True)
    quantity = fields.Int(required=True)
    image_url = fields.Str()
    category_id = fields.Int()

class InvoiceItemSchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    unit_price = fields.Float()
    subtotal = fields.Float()

class InvoiceSchema(Schema):
    id = fields.Int(dump_only=True)
    customer_name = fields.Str()
    created_by_id = fields.Int()
    total = fields.Float()
    items = fields.List(fields.Nested(InvoiceItemSchema))
