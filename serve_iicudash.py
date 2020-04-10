from waitress import serve
import iicudash
serve(iicudash.create_app(), host='127.0.0.1', port='8003')