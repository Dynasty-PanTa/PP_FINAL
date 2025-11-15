from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import Invoice, InvoiceItem, Product

inv_ns = Namespace("invoices", description="Sales Invoice Management", security="Bearer Auth")

# Swagger model for multiple items
item_model = inv_ns.model("InvoiceItemInput", {
    "product_id": fields.Integer(required=True),
    "quantity": fields.Integer(required=True)
})

invoice_model = inv_ns.model("InvoiceInput", {
    "customer_name": fields.String(required=True),
    "customer_phone": fields.String(),
    "customer_address": fields.String(),
    "items": fields.List(fields.Nested(item_model), required=True)
})

@inv_ns.route("")
class InvoiceList(Resource):

    @jwt_required()
    def get(self):
        """List all invoices"""
        invoices = Invoice.query.all()
        result = []
        for inv in invoices:
            result.append({
                "id": inv.id,
                "customer_name": inv.customer_name,
                "customer_phone": inv.customer_phone,
                "customer_address": inv.customer_address,
                "items": [
                    {
                        "product_id": i.product_id,
                        "product_name": i.product.name if i.product else None,
                        "quantity": i.quantity,
                        "unit_price": i.unit_price_cents / 100.0,
                        "subtotal": i.subtotal_cents / 100.0
                    } for i in inv.items
                ],
                "total": inv.total_cents / 100.0
            })
        return result, 200

    @jwt_required()
    @inv_ns.expect(invoice_model)
    def post(self):
        """Create a new sale/invoice"""
        data = request.json
        customer_name = data.get("customer_name")
        customer_phone = data.get("customer_phone")
        customer_address = data.get("customer_address")
        items = data.get("items", [])

        if not items:
            return {"message": "At least one item is required"}, 400

        new_invoice = Invoice(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address
        )
        db.session.add(new_invoice)
        db.session.flush()  # get invoice ID

        total_cents = 0

        for it in items:
            product_id = it.get("product_id")
            quantity = it.get("quantity")
            product = Product.query.get(product_id)
            if not product:
                db.session.rollback()
                return {"message": f"Invalid product_id: {product_id}"}, 400

            unit_price_cents = product.price_cents
            subtotal_cents = unit_price_cents * quantity
            total_cents += subtotal_cents

            invoice_item = InvoiceItem(
                invoice_id=new_invoice.id,
                product_id=product.id,
                quantity=quantity,
                unit_price_cents=unit_price_cents,
                subtotal_cents=subtotal_cents
            )
            db.session.add(invoice_item)

        new_invoice.total_cents = total_cents
        db.session.commit()
        return {"message": "Invoice created", "id": new_invoice.id}, 201


@inv_ns.route("/<int:id>")
class InvoiceDetail(Resource):

    @jwt_required()
    def get(self, id):
        """Get single invoice by ID"""
        inv = Invoice.query.get_or_404(id)
        return {
            "id": inv.id,
            "customer_name": inv.customer_name,
            "customer_phone": inv.customer_phone,
            "customer_address": inv.customer_address,
            "items": [
                {
                    "product_id": i.product_id,
                    "product_name": i.product.name if i.product else None,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price_cents / 100.0,
                    "subtotal": i.subtotal_cents / 100.0
                } for i in inv.items
            ],
            "total": inv.total_cents / 100.0
        }, 200

    @jwt_required()
    @inv_ns.expect(invoice_model)
    def put(self, id):
        """Update existing sale/invoice"""
        inv = Invoice.query.get_or_404(id)
        data = request.json
        inv.customer_name = data.get("customer_name", inv.customer_name)
        inv.customer_phone = data.get("customer_phone", inv.customer_phone)
        inv.customer_address = data.get("customer_address", inv.customer_address)

        # Clear existing items
        InvoiceItem.query.filter_by(invoice_id=id).delete()

        items = data.get("items", [])
        total_cents = 0

        for it in items:
            product_id = it.get("product_id")
            quantity = it.get("quantity")
            product = Product.query.get(product_id)
            if not product:
                db.session.rollback()
                return {"message": f"Invalid product_id: {product_id}"}, 400

            unit_price_cents = product.price_cents
            subtotal_cents = unit_price_cents * quantity
            total_cents += subtotal_cents

            invoice_item = InvoiceItem(
                invoice_id=inv.id,
                product_id=product.id,
                quantity=quantity,
                unit_price_cents=unit_price_cents,
                subtotal_cents=subtotal_cents
            )
            db.session.add(invoice_item)

        inv.total_cents = total_cents
        db.session.commit()
        return {"message": "Invoice updated", "id": inv.id}, 200

    @jwt_required()
    def delete(self, id):
        """Delete a sale/invoice"""
        inv = Invoice.query.get_or_404(id)
        try:
            InvoiceItem.query.filter_by(invoice_id=id).delete()
            db.session.delete(inv)
            db.session.commit()
            return {"message": "Invoice deleted"}, 200
        except Exception as e:
            db.session.rollback()
            return {"message": f"Internal Server Error: {str(e)}"}, 500
