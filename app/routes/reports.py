from flask import request
from flask_restx import Namespace, Resource
from ..models import Invoice, InvoiceItem, Product, User
from ..extensions import db
from sqlalchemy import func
import datetime

rep_ns = Namespace('reports', description='Reporting')


@rep_ns.route('/sales')
class SalesReport(Resource):
    def get(self):
        """
        Generate aggregated sales report by daily, weekly, or monthly
        Query params:
        start: YYYY-MM-DD
        end: YYYY-MM-DD
        range: daily | weekly | monthly
        """
        start = request.args.get('start')
        end = request.args.get('end')
        range_type = request.args.get('range', 'daily')

        q = db.session.query(Invoice)

        if start:
            start_dt = datetime.datetime.fromisoformat(start)
            q = q.filter(Invoice.created_at >= start_dt)
        if end:
            end_dt = datetime.datetime.fromisoformat(end) + datetime.timedelta(days=1)
            q = q.filter(Invoice.created_at < end_dt)

        if range_type == 'daily':
            grp = func.strftime('%Y-%m-%d', Invoice.created_at)
        elif range_type == 'monthly':
            grp = func.strftime('%Y-%m', Invoice.created_at)
        else:  # weekly
            grp = func.strftime('%Y-%W', Invoice.created_at)

        rows = db.session.query(
            grp.label('period'),
            func.sum(Invoice.total_cents).label('total')
        ).filter(
            Invoice.id.in_(q.with_entities(Invoice.id))
        ).group_by('period').order_by('period').all()

        return [{'period': r[0], 'total': r[1] / 100.0 if r[1] else 0} for r in rows], 200


@rep_ns.route('/sales-by')
class SalesBy(Resource):
    def get(self):
        """
        Generate detailed sales report by product, category, or user
        Query params:
        by: product | category | user
        start: YYYY-MM-DD
        end: YYYY-MM-DD
        """
        by = request.args.get('by', 'product')
        start = request.args.get('start')
        end = request.args.get('end')

        q = db.session.query(InvoiceItem, Invoice, Product, User).join(
            Invoice, InvoiceItem.invoice_id == Invoice.id
        ).join(
            Product, InvoiceItem.product_id == Product.id
        ).outerjoin(
            User, Invoice.created_by_id == User.id
        )

        if start:
            start_dt = datetime.datetime.fromisoformat(start)
            q = q.filter(Invoice.created_at >= start_dt)
        if end:
            end_dt = datetime.datetime.fromisoformat(end) + datetime.timedelta(days=1)
            q = q.filter(Invoice.created_at < end_dt)

        result = []

        for item, invoice, product, user in q.all():
            row = {
                "product": product.name,
                "total": item.subtotal_cents / 100.0,
                "sale_by": user.username if user else "Unknown",
                "date_time": invoice.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            result.append(row)

        # Optionally, group by category or user if requested
        if by == 'category':
            grouped = {}
            for r in result:
                cat_name = Product.query.filter_by(name=r['product']).first().category.name
                if cat_name not in grouped:
                    grouped[cat_name] = 0
                grouped[cat_name] += r['total']
            result = [{"category": k, "total": v} for k, v in grouped.items()]

        elif by == 'user':
            grouped = {}
            for r in result:
                user_name = r['sale_by']
                if user_name not in grouped:
                    grouped[user_name] = 0
                grouped[user_name] += r['total']
            result = [{"user": k, "total": v} for k, v in grouped.items()]

        return result, 200
