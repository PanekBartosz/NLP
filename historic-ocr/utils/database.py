import os
from supabase import create_client

def initialize_supabase():
    """Inicjalizacja klienta Supabase"""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("Brakuje zmiennych środowiskowych SUPABASE_URL i SUPABASE_KEY")
    
    return create_client(supabase_url, supabase_key)

def insert_result(supabase, result_data):
    """Wstawianie wyników do bazy danych"""
    return supabase.table('ocr_results').insert(result_data).execute()

def get_result(supabase, result_id):
    """Pobieranie wyniku po ID"""
    response = supabase.table('ocr_results').select('*').eq('id', result_id).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None

def get_all_results(supabase):
    """Pobieranie wszystkich wyników"""
    response = supabase.table('ocr_results').select('id,created_at,filename').order('created_at', desc=True).execute()
    return response.data if response.data else []
