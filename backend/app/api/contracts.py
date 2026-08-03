from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.contract import (
    ContractResponse,
    ContractListResponse,
    ContractDetailResponse,
    ContractUploadResponse,
    ContractUpdate,
)
from app.services.contract_service import ContractService

router = APIRouter()
contract_service = ContractService()


@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(
    file: UploadFile = File(...),
    title: str = Form(...),
    contract_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a new contract document
    
    - **file**: Contract document file (PDF, DOCX, etc.)
    - **title**: Contract title
    - **contract_type**: Optional contract type
    """
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Create contract
        contract = contract_service.create_contract(
            db=db,
            file_obj=file.file,
            title=title,
            contract_type=contract_type,
        )
        
        return ContractUploadResponse(
            message="Contract uploaded successfully",
            contract_id=contract.id,
            file_name=contract.file_name,
            status=contract.status,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ContractListResponse)
async def list_contracts(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    contract_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List all contracts with optional filtering
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by status (pending, processing, completed, failed)
    - **contract_type**: Filter by contract type
    """
    contracts = contract_service.list_contracts(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        contract_type=contract_type,
    )
    
    total = len(contracts)  # In production, use count query
    
    return ContractListResponse(
        contracts=[ContractResponse.from_orm(c) for c in contracts],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/{contract_id}", response_model=ContractDetailResponse)
async def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific contract
    
    - **contract_id**: Contract ID
    """
    contract = contract_service.get_contract(db=db, contract_id=contract_id)
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return ContractDetailResponse.from_orm(contract)


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    contract_update: ContractUpdate,
    db: Session = Depends(get_db),
):
    """
    Update contract metadata
    
    - **contract_id**: Contract ID
    - **contract_update**: Updated contract data
    """
    contract = contract_service.get_contract(db=db, contract_id=contract_id)
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Update fields
    update_data = contract_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)
    
    db.commit()
    db.refresh(contract)
    
    return ContractResponse.from_orm(contract)


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a contract
    
    - **contract_id**: Contract ID
    """
    success = contract_service.delete_contract(db=db, contract_id=contract_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return {"message": "Contract deleted successfully"}


@router.get("/{contract_id}/clauses")
async def get_contract_clauses(
    contract_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all clauses for a contract
    
    - **contract_id**: Contract ID
    """
    contract = contract_service.get_contract(db=db, contract_id=contract_id)
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    clauses = contract_service.get_contract_clauses(db=db, contract_id=contract_id)
    
    return {
        "contract_id": contract_id,
        "clauses": [clause.to_dict() for clause in clauses],
        "total": len(clauses),
    }


@router.get("/{contract_id}/sections")
async def get_contract_sections(
    contract_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all sections for a contract
    
    - **contract_id**: Contract ID
    """
    contract = contract_service.get_contract(db=db, contract_id=contract_id)
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    sections = contract_service.get_contract_sections(db=db, contract_id=contract_id)
    
    return {
        "contract_id": contract_id,
        "sections": [section.to_dict() for section in sections],
        "total": len(sections),
    }


@router.post("/{contract_id}/reprocess")
async def reprocess_contract(
    contract_id: int,
    db: Session = Depends(get_db),
):
    """
    Reprocess a contract document
    
    - **contract_id**: Contract ID
    """
    try:
        contract = contract_service.process_contract(db=db, contract_id=contract_id)
        
        return {
            "message": "Contract reprocessed successfully",
            "contract_id": contract.id,
            "status": contract.status,
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/")
async def search_contracts(
    q: str,
    db: Session = Depends(get_db),
):
    """
    Search contracts by title or content
    
    - **q**: Search query
    """
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    contracts = contract_service.search_contracts(db=db, search_term=q)
    
    return {
        "query": q,
        "contracts": [ContractResponse.from_orm(c) for c in contracts],
        "total": len(contracts),
    }

# Made with Bob
