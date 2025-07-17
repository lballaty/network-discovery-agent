# Load scan configurations from Supabase
from .supabase_client import supabase

def load_configs():
    resp = supabase.table('scan_configs').select('*').execute()
    return resp.data
