from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from app.services.document_service import document_service

router = APIRouter()


@router.post("/process-zip", summary="Processa um arquivo ZIP com vários .txt")
async def process_zip(file: UploadFile = File(...)):
    """
            Recebe um arquivo ZIP contendo vários arquivos .txt com informações de documentos.
            Lê cada arquivo, detecta encoding, verifica anomalias e retorna uma planilha Excel (.xlsx) com os dados click em Try it out para utilizar.


            O formado dos arquivos .txt deve ser o seguinte:
    ```
        TIPO_DOCUMENTO: NOTA_FISCAL
        NUMERO_DOCUMENTO: NF-78432
        DATA_EMISSAO: 15/04/2024
        FORNECEDOR: TechSoft Ltda
        CNPJ_FORNECEDOR: 12.345.678/0001-90
        DESCRICAO_SERVICO: Licença de Software ERP
        VALOR_BRUTO: R$ 15.000,00
        DATA_PAGAMENTO: 20/04/2024
        DATA_EMISSAO_NF: 15/04/2024
        APROVADO_POR: Maria Silva
        BANCO_DESTINO: Banco do Brasil Ag.1234 C/C 56789-0
        STATUS: PAGO
        HASH_VERIFICACAO: NLC042338471
    ```
    """
    # Validar se o arquivo é um ZIP
    if not isinstance(file.filename, str) or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado é inválido. O arquivo precisa ser .zip",
        )

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
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Em produção, você logaria isso adequadamente
        raise HTTPException(
            status_code=500, detail=f"Erro interno ao processar o arquivo: {str(e)}"
        )
