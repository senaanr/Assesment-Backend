import json
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:senanur102@localhost:5432/assignment'
db = SQLAlchemy(app)

class Report(db.Model):
    __tablename__ = 'report_output'
    row = db.Column(db.BigInteger, primary_key=True, nullable=False, unique=True)
    main_uploaded_variation = db.Column(db.String, nullable=False)
    main_existing_variation = db.Column(db.String, nullable=False)
    main_symbol = db.Column(db.String, nullable=False)
    main_af_vcf = db.Column(db.Numeric, nullable=False)
    main_dp = db.Column(db.Numeric, nullable=False)
    details2_provean = db.Column(db.String, nullable=False)
    details2_dann_score = db.Column(db.Numeric, nullable=True)
    links_mondo = db.Column(db.String, nullable=False)
    links_pheno_pubmed = db.Column(db.String, nullable=False)

    def __init__(self, row, main_uploaded_variation, main_existing_variation, main_symbol,
                 main_af_vcf, main_dp, details2_provean, details2_dann_score,
                 links_mondo, links_pheno_pubmed):
        self.row = row
        self.main_uploaded_variation = main_uploaded_variation
        self.main_existing_variation = main_existing_variation
        self.main_symbol = main_symbol
        self.main_af_vcf = main_af_vcf
        self.main_dp = main_dp
        self.details2_provean = details2_provean
        self.details2_dann_score = details2_dann_score
        self.links_mondo = links_mondo
        self.links_pheno_pubmed = links_pheno_pubmed

@app.route('/', methods=['GET', 'POST'])
def query():
    if request.method == 'POST':
        try:
            # Filtreleri ve sıralamayı al
            data = request.get_json()
            ordering = data.get('ordering', [])
            page = data.get('page', 1)
            page_size = data.get('page_size', 10)

            # SQL sorgusunu oluştur
            query = db.session.query(Report)

            # Filtreleri al
            filters = data.get('filters', {})

            if filters:
                # Filtreler için bir liste oluştur
                filter_list = []

                # Her bir filtre için SQL sorgusunu oluştur
                for column, value in filters.items():
                    if isinstance(getattr(Report, column).type, db.Numeric):  # Check if the column is of Numeric type
                        # For Numeric columns, use regular equality instead of ILIKE
                        filter_list.append(getattr(Report, column) == value)
                    else:
                        # For other columns, use ILIKE
                        filter_list.append(getattr(Report, column).ilike(f"%{value}%"))

                # Filtreleri 'veya' (OR) bağlacıyla birleştir
                query = query.filter(or_(*filter_list))

            if ordering:
                for order in ordering:
                    if isinstance(order, dict):
                        column, direction = order.popitem()
                    else:
                        # If order is just a string, split it by ',' to handle multiple columns
                        columns = order.split(',')
                        print(f"Received columns: {columns}")
                        for column in columns:
                            try:
                                order_attribute = getattr(Report, column)
                                query = query.order_by(order_attribute.desc() if direction == 'desc' else order_attribute)
                            except AttributeError:
                                print(f"Invalid column name: {column}")
                                return jsonify({'error': f'Invalid column name: {column}'}), 400

            # Sayfalama işlemi
            offset = (page - 1) * page_size
            query = query.limit(page_size).offset(offset)

            # Sonuçları al
            results = query.all()

            results_dicts = [row.__dict__ for row in results]

            # Remove the '_sa_instance_state' key from each dictionary
            results_dicts_cleaned = [{key: value for key, value in row.items() if key != '_sa_instance_state'} for row in results_dicts]

            # Toplam veri sayısını al
            total_count = query.count()

            # JSON yanıtını oluştur
            response = {
                'page': page,
                'page_size': page_size,
                'count': total_count,
                'results': results_dicts_cleaned
            }

            return jsonify(response)

        except Exception as e:
            import traceback
            traceback.print_exc()  # Print the traceback for debugging purposes
            return jsonify({'error': str(e)}), 500

    # GET request ise, template'e geçirilecek olan 'reports' değişkenini oluştur
    reports = Report.query.paginate(per_page=20, page=request.args.get('page', 1, type=int))

    return render_template('home.html', reports=reports)

if __name__ == '__main__':
    app.run(debug=True)