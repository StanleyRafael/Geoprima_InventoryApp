from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from collections import defaultdict

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/geoprima_inventory'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)# Database connection
migrate = Migrate(app, db)

@app.route('/')
def login():
    return render_template('loginPage.html')

class ItemList(db.Model):
    def to_dict(self):
        return {
            "id": self.id,
            "nama_barang": self.nama_barang,
            "tanggal_masuk": self.tanggal_masuk.strftime('%Y-%m-%d') if self.tanggal_masuk else '',
            "tanggal_keluar": self.tanggal_keluar.strftime('%Y-%m-%d') if self.tanggal_keluar else '',
            "nomor_seri": self.nomor_seri,
            "nama_pembeli_pemasok": self.nama_pembeli_pemasok,
            "nama_pembeli": self.nama_pembeli,
            "tipe_barang": self.tipe_barang,
            "source_type": self.source_type,
            "partial" : self.partial
        }
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_barang = db.Column(db.String(100), nullable=False)
    tanggal_masuk = db.Column(db.Date, nullable=True)
    tanggal_keluar = db.Column(db.Date, nullable=True)
    nomor_seri = db.Column(db.String(50), nullable=False)
    nama_pembeli_pemasok = db.Column(db.String(100), nullable=False)
    nama_pembeli = db.Column(db.String(100), nullable=False)
    source_type = db.Column(db.String(20), nullable=False)
    tipe_barang = db.Column(db.String(255), nullable=True)  # Comma-separated type
    partial = db.Column(db.Boolean, default=False)


    # Relationship with components, with cascade delete
    components = db.relationship('Component', backref='item', lazy=True, cascade="all, delete")

class Component(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_list.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('component.id'), nullable=True)  # Self-referencing for sub-components
    component_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # Relationship for sub-components
    sub_components = db.relationship('Component', backref=db.backref('parent', remote_side=[id]), lazy=True)

@app.route('/dashboard')
def dashboard():
    items = ItemList.query.all()

    items_data = defaultdict(lambda: {"jumlah": 0, "nama_barang": ""})

    # Count occurrences of each item by name
    for item in items:
        items_data[item.nama_barang]["jumlah"] += 1
        items_data[item.nama_barang]["nama_barang"] = item.nama_barang

    # Convert defaultdict to a regular list
    unique_items = [{"nama_barang": name, "jumlah": data["jumlah"]} for name, data in items_data.items()]

    return render_template('Dashboard.html', items=items, unique_items=unique_items)

@app.route('/api/items')
def get_items():
    items = ItemList.query.all()
    items_data = [item.to_dict() for item in items]

    # Dictionary to count items with the same name, source_type, and a single `tipe_barang`
    items_data_count = defaultdict(lambda: {"jumlah": 0, "nama_barang": "", "tipe_barang": "", "source_type": ""})

    for item in items:
        types = item.tipe_barang.split(',') if item.tipe_barang else []

        for tipe in types:
            tipe = tipe.strip()  # Clean whitespace around `tipe_barang`
            
            # Create a unique key for each `tipe_barang`
            key = (item.nama_barang, item.source_type, tipe)

            # Increment count and populate data for the specific `tipe_barang`
            items_data_count[key]["jumlah"] += 1
            items_data_count[key]["nama_barang"] = item.nama_barang
            items_data_count[key]["tipe_barang"] = tipe
            items_data_count[key]["source_type"] = item.source_type

    # Convert the dictionary to a list format suitable for JSON response
    unique_items = [
        {
            "nama_barang": data["nama_barang"],
            "tipe_barang": data["tipe_barang"],
            "jumlah": data["jumlah"],
            "source_type": data["source_type"]
        }
        for data in items_data_count.values()
    ]

    return jsonify({
        'items_data': items_data,
        'unique_items2': unique_items,
        'status': 'success'
    })

@app.route('/submit-item', methods=['POST'])
def submit_item():
    data = request.get_json()
    
    # Convert 'tipe_barang' array into a comma-separated string
    tipe_barang = ','.join(data['tipe_barang']) if data.get('tipe_barang') else None
    
    source_type = data.get('source_type', 'unknown')

    # Create a new item and commit it to get the item ID
    new_item = ItemList(
        nama_barang=data['nama_barang'],
        tanggal_masuk=data['tanggal_masuk'] if data['tanggal_masuk'] else None,
        nomor_seri=data['nomor_seri'],
        nama_pembeli_pemasok=data['nama_pembeli_pemasok'],
        tipe_barang=tipe_barang,
        source_type=source_type
    )
    
    db.session.add(new_item)
    db.session.commit()  # Commit to get the new_item.id for foreign key usage

    # Save components and sub-components related to this item
    for component_data in data['components']:
        if component_data['name']:  # Only save non-empty component names
            # Save the main component first
            new_component = Component(
                item_id=new_item.id,  # Use the item's ID as foreign key
                component_name=component_data['name'],
                quantity=component_data['quantity'],
                parent_id=None  # This is the main component, so no parent
            )
            db.session.add(new_component)
            db.session.commit()  # Commit to get the new_component.id for sub-components

            # Now save any sub-components related to this main component
            for sub_component_data in component_data.get('sub_components', []):
                new_sub_component = Component(
                    item_id=new_item.id,  # Same item_id for the sub-component
                    component_name=sub_component_data['name'],
                    quantity=sub_component_data['quantity'],
                    parent_id=new_component.id  # Set the parent_id as the main component's id
                )
                db.session.add(new_sub_component)

    db.session.commit()  # Commit all changes

    return jsonify({"message": "Item and components submitted successfully!"})

@app.route('/submit-jual-item', methods=['POST'])
def submit_jual_item():
    data = request.get_json()
    
    # Convert 'tipe_barang' array into a comma-separated string
    tipe_barang = ','.join(data['tipe_barang']) if data.get('tipe_barang') else None

    source_type = data.get('source_type', 'unknown')
    
    # Create a new item and commit it to get the item ID
    new_item = ItemList(
        nama_barang=data['nama_barang'],
        tanggal_keluar=data['tanggal_keluar'] if data['tanggal_keluar'] else None,
        nomor_seri=data['nomor_seri'],
        nama_pembeli_pemasok=data['nama_pembeli_pemasok'],
        tipe_barang=tipe_barang,
        source_type=source_type
    )
    
    db.session.add(new_item)
    db.session.commit()  # Commit to get the new_item.id for foreign key usage

    # Save components related to this item
    for component_data in data['components']:
        if component_data['name']:  # Only save non-empty component names
            # Save the main component first
            new_component = Component(
                item_id=new_item.id,  # Use the item's ID as foreign key
                component_name=component_data['name'],
                quantity=component_data['quantity'],
                parent_id=None  # This is the main component, so no parent
            )
            db.session.add(new_component)
            db.session.commit()  # Commit to get the new_component.id for sub-components

            # Now save any sub-components related to this main component
            for sub_component_data in component_data.get('sub_components', []):
                if sub_component_data['name']:  # Only save non-empty sub-component names
                    new_sub_component = Component(
                        item_id=new_item.id,  # Same item_id for the sub-component
                        component_name=sub_component_data['name'],
                        quantity=sub_component_data['quantity'],
                        parent_id=new_component.id  # Set the parent_id as the main component's id
                    )
                    db.session.add(new_sub_component)

    db.session.commit()  # Commit all changes

    return jsonify({"message": "Item and components submitted successfully!"})

@app.route('/api/components/<int:item_id>')
def get_components(item_id):
    components = Component.query.filter_by(item_id=item_id, parent_id=None).all()  # Get top-level components only
    components_data = []

    def serialize_component(component):
        # Recursive function to get subcomponents
        return {
            "id": component.id,
            "component_name": component.component_name,
            "quantity": component.quantity,
            "originalQuantity": component.quantity,
            "sub_components": [serialize_component(sub) for sub in component.sub_components]
        }

    for component in components:
        components_data.append(serialize_component(component))

    return jsonify(components_data)

@app.route('/edit-item/<int:id>', methods=['POST'])
def edit_item(id):
    data = request.json
    item = ItemList.query.get_or_404(id)
    
    item.nama_barang = data['nama_barang']
    item.tanggal_masuk = data['tanggal_masuk']
    item.tanggal_keluar = data['tanggal_keluar']
    item.nomor_seri = data['nomor_seri']
    item.nama_pembeli_pemasok = data['nama_pembeli_pemasok']
    item.tipe_barang = ','.join(data['tipe_barang']) if data.get('tipe_barang') else None
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/delete-item/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = ItemList.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()  # Rollback if there's an error
        return jsonify({"error": str(e)}), 500

@app.route('/api/autocomplete-items', methods=['GET'])
def autocomplete_items():
    search_query = request.args.get('query', '')
    
    items = (
        ItemList.query
        .filter(ItemList.nama_barang.ilike(f"%{search_query}%"))
        .filter(ItemList.source_type == 'beli')  # Add source_type filter so that sold items won't appear here
        .all()
    )
    
    # Prepare response data
    items_data = [
        {
            "id": item.id,
            "nama_barang": item.nama_barang,
            "nomor_seri": item.nomor_seri,
            "nama_pembeli_pemasok": item.nama_pembeli_pemasok,
            "tipe_barang": item.tipe_barang.split(',') if item.tipe_barang else [],
        }
        for item in items
    ]
    return jsonify(items_data)

@app.route('/update-source-type/<int:id>', methods=['POST'])
def update_source_type(id):
    try:
        data = request.json  # Capture request payload
        item = ItemList.query.get_or_404(id)

        # Update source type and buyer's name
        item.source_type = data.get('source_type', item.source_type)
        if 'nama_pembeli' in data:  # Only update if the field is filled
            item.nama_pembeli = data['nama_pembeli']
        if 'tanggal_keluar' in data:  # Only update if the field is filled
            item.tanggal_keluar = data['tanggal_keluar']

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating source type: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/process-partial-sell', methods=['POST'])
def process_partial_sell():
    try:
        data = request.json
        print(data)  # Log the received data
        original_item = ItemList.query.get_or_404(data['itemId'])

        # Update original item's components
        for component_data in data['components']:
            component = Component.query.get_or_404(component_data['id'])
            component.quantity = component_data['remainingQuantity']  # Update remaining quantity

        # Update original item's sub-components
        for sub_component_data in data.get('subComponents', []):
            sub_component = Component.query.get_or_404(sub_component_data['id'])
            sub_component.quantity = sub_component_data['remainingQuantity']  # Update remaining quantity

        # Create a new "jual" item with the sold components and sub-components
        sold_item = ItemList(
            nama_barang=original_item.nama_barang,
            tanggal_masuk=original_item.tanggal_masuk,
            tanggal_keluar=data['tanggal_keluar'],
            nomor_seri=original_item.nomor_seri,
            nama_pembeli_pemasok=original_item.nama_pembeli_pemasok,
            nama_pembeli=data['nama_pembeli'],
            source_type='jual',
            tipe_barang=original_item.tipe_barang
        )
        db.session.add(sold_item)
        db.session.commit()

        # Add sold components to the new item
        for component_data in data['components']:
            if component_data['soldQuantity'] > 0:  # Only add sold components
                sold_component = Component(
                    component_name=Component.query.get_or_404(component_data['id']).component_name,
                    quantity=component_data['soldQuantity'],
                    parent_id=None,  # Top-level component
                    item_id=sold_item.id,
                )
                db.session.add(sold_component)
                

        # Add sold sub-components to the new item
        for sub_component_data in data.get('subComponents', []):
            if sub_component_data['soldQuantity'] > 0:  # Only add sold sub-components
                sold_sub_component = Component(
                    component_name=Component.query.get_or_404(sub_component_data['id']).component_name,
                    quantity=sub_component_data['soldQuantity'],
                    parent_id=sold_component.id,
                    item_id=sold_item.id,
                )
                db.session.add(sold_sub_component)

        original_item.partial = True

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error processing partial sell: {e}")  # Log the error
        return jsonify({'success': False, 'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
