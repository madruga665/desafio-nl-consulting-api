from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from app.services.document_service import document_service

router = APIRouter()

@router.post("/process-zip", summary="Processa um arquivo ZIP com vários .txt")
async def process_zip(file: UploadFile = File(...)):
    """
    Recebe um arquivo ZIP contendo vários arquivos .txt com informações de documentos.
    Lê cada arquivo, detecta encoding, verifica anomalias e retorna uma planilha Excel (.xlsx) com os dados.
    """
    # Validar se o arquivo é um ZIP
    if not isinstance(file.filename, str) or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="O arquivo enviado é inválido. O arquivo precisa ser .zip")

    try:
        # Ler o conteúdo do arquivo
        zip_content = await file.read()
        
        # Chamar o serviço de processamento
        excel_data = await document_service.process_zip_file(zip_content)
        
        # Retornar o arquivo Excel para download
        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=processamento_{file.filename}.xlsx"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Em produção, você logaria isso adequadamente
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o arquivo: {str(e)}")
