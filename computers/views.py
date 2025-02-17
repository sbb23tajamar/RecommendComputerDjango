from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
import os
from .utils import extract_data_from_pdf, validate_data, create_table, insert_computer, chatbot_response

def inicio(request):
    return render(request, 'computers/home.html')

def upload_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        file_path = os.path.join('uploads', pdf_file.name)
        
        # Guardar el archivo temporalmente
        saved_path = default_storage.save(file_path, ContentFile(pdf_file.read()))
        full_path = default_storage.path(saved_path)
        
        try:
            # Procesar el archivo PDF
            data = extract_data_from_pdf(full_path)
            if not data:
                return render(request, 'computers/pdf.html', {'error': 'No data extracted from the PDF'})
            
            # Validar los datos
            validated_data = validate_data(data)
            if not validated_data:
                return render(request, 'computers/pdf.html', {'error': 'Data validation failed'})
            
            # Insertar en la base de datos
            create_table()
            insert_computer(validated_data)
            
            return render(request, 'computers/pdf.html', {'message': 'Data inserted successfully'})
        
        except FileNotFoundError:
            return render(request, 'computers/pdf.html', {'error': f'The file {pdf_file.name} was not found'})
        except Exception as e:
            return render(request, 'computers/pdf.html', {'error': str(e)})
        
        finally:
            # Eliminar el archivo después de procesarlo
            default_storage.delete(saved_path)
    
    return render(request, 'computers/pdf.html')


def chatbot(request):
    if request.method == 'POST':
        user_input = request.POST.get('user_input', '').strip()
        if not user_input:
            return JsonResponse({'error': 'No input provided'}, status=400)
        
        if user_input.lower() == 'exit':
            return JsonResponse({'message': 'Chatbot session ended'})
        
        response = chatbot_response(user_input)
        return JsonResponse({'response': response})
    
    return render(request, 'computers/chat.html')