# # # from fastapi import APIRouter, HTTPException
# # # from fastapi.responses import JSONResponse
# # # import xmlrpc.client

# # # router = APIRouter(prefix="/dashboard/bom", tags=["BOM"])

# # # # Odoo connection settings
# # # url = 'https://modula12.odoo.com'
# # # db = 'modula12'
# # # username = 'admin@ayena.in'
# # # password = '1'

# # # # Initialize Odoo connection
# # # common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
# # # uid = common.authenticate(db, username, password, {})
# # # models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# # # def safe_extract_id(m2o_value):
# # #     """Safely extract integer ID from Many2one field."""
# # #     if not m2o_value or m2o_value == [False, False]:
# # #         return False
# # #     if isinstance(m2o_value, list) and len(m2o_value) >= 1:
# # #         id_val = m2o_value[0]
# # #         if isinstance(id_val, int):
# # #             return id_val
# # #     return False

# # # @router.get("/{sales_order}/{cabinet_position}")
# # # async def get_bom_items(sales_order: str, cabinet_position: str):
# # #     try:
# # #         bom_data = fetch_full_bom_data(sales_order, cabinet_position)
# # #         return JSONResponse(content=bom_data)
# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# # # def fetch_full_bom_data(sales_order: str, cabinet_position: str):
# # #     # Fetch sale.order.line items
# # #     sale_lines = models.execute_kw(
# # #         db, uid, password,
# # #         'sale.order.line', 'search_read',
# # #         [[('order_id.name', '=', sales_order), ('x_studio_cabinet_position', '=', cabinet_position)]],
# # #         {'fields': ['id', 'name', 'product_id', 'x_studio_cabinet_position', 'product_uom_qty', 'product_uom']}
# # #     )

# # #     if not sale_lines:
# # #         raise HTTPException(status_code=404, detail="No BOM items found.")

# # #     def explode_bom(product_id, product_tmpl_id, quantity=1.0, depth=0, max_depth=10, visited_boms=None):
# # #         """
# # #         Recursively explode BOM to get all components.
# # #         visited_boms: set of bom_id to prevent infinite loops
# # #         """
# # #         if visited_boms is None:
# # #             visited_boms = set()
            
# # #         if depth > max_depth:
# # #             print(f"Max recursion depth {max_depth} reached")
# # #             return []
            
# # #         # Find applicable BOM
# # #         domain = [('product_tmpl_id', '=', product_tmpl_id)]
# # #         if product_id:
# # #             domain = ['|', ('product_id', '=', product_id)] + domain

# # #         boms = models.execute_kw(
# # #             db, uid, password,
# # #             'mrp.bom', 'search_read',
# # #             [domain],
# # #             {'fields': ['id', 'product_id', 'product_tmpl_id', 'product_qty', 'product_uom_id'], 'limit': 1}
# # #         )

# # #         if not boms:
# # #             # No BOM found - this is a leaf component
# # #             return []
        
# # #         bom = boms[0]
# # #         bom_id = bom['id']
        
# # #         # Check for cycles
# # #         if bom_id in visited_boms:
# # #             print(f"Cycle detected: BOM {bom_id} already visited")
# # #             return []
            
# # #         visited_boms.add(bom_id)
# # #         print(f"Depth {depth}: Processing BOM {bom_id} for product_tmpl_id {product_tmpl_id}")

# # #         # Fetch BOM lines (the actual components)
# # #         bom_lines = models.execute_kw(
# # #             db, uid, password,
# # #             'mrp.bom.line', 'search_read',
# # #             [[('bom_id', '=', bom_id)]],
# # #             {'fields': ['id', 'product_id', 'product_qty', 'product_uom_id', 'bom_id']}
# # #         )

# # #         result = []
# # #         for line in bom_lines:
# # #             line_product_id = safe_extract_id(line.get('product_id'))
# # #             line_qty = line.get('product_qty', 0)
            
# # #             # Get product template for this component
# # #             if line_product_id:
# # #                 product = models.execute_kw(
# # #                     db, uid, password,
# # #                     'product.product', 'read',
# # #                     [[line_product_id]],
# # #                     {'fields': ['product_tmpl_id', 'name']}
# # #                 )
                
# # #                 if product:
# # #                     line_product_tmpl_id = safe_extract_id(product[0].get('product_tmpl_id'))
                    
# # #                     component = {
# # #                         'bom_line_id': line['id'],
# # #                         'product_id': line_product_id,
# # #                         'product_name': product[0].get('name'),
# # #                         'quantity': line_qty * quantity,  # Multiply by parent quantity
# # #                         'uom': line.get('product_uom_id'),
# # #                         'depth': depth,
# # #                         'children': []
# # #                     }
                    
# # #                     # Recursively explode if this component has its own BOM
# # #                     child_components = explode_bom(
# # #                         line_product_id, 
# # #                         line_product_tmpl_id, 
# # #                         line_qty * quantity,
# # #                         depth + 1, 
# # #                         max_depth,
# # #                         visited_boms.copy()  # Pass a copy to allow reuse in other branches
# # #                     )
                    
# # #                     if child_components:
# # #                         component['children'] = child_components
                    
# # #                     result.append(component)
        
# # #         return result

# # #     # Process each sale order line
# # #     processed_items = []
# # #     for line in sale_lines:
# # #         product_id = safe_extract_id(line.get('product_id'))
# # #         quantity = line.get('product_uom_qty', 1.0)
        
# # #         if product_id:
# # #             # Get product template
# # #             product = models.execute_kw(
# # #                 db, uid, password,
# # #                 'product.product', 'read',
# # #                 [[product_id]],
# # #                 {'fields': ['product_tmpl_id', 'name']}
# # #             )
            
# # #             if product:
# # #                 product_tmpl_id = safe_extract_id(product[0].get('product_tmpl_id'))
                
# # #                 item = {
# # #                     'sale_line_id': line['id'],
# # #                     'product_id': product_id,
# # #                     'product_name': product[0].get('name'),
# # #                     'cabinet_position': line.get('x_studio_cabinet_position'),
# # #                     'quantity': quantity,
# # #                     'uom': line.get('product_uom'),
# # #                     'children': explode_bom(product_id, product_tmpl_id, quantity)
# # #                 }
                
# # #                 processed_items.append(item)
    
# # #     return processed_items


# # from fastapi import APIRouter, HTTPException
# # from fastapi.responses import JSONResponse
# # import xmlrpc.client

# # router = APIRouter(prefix="/dashboard/bom", tags=["BOM"])

# # # Odoo connection settings
# # url = 'https://modula12.odoo.com'
# # db = 'modula12'
# # username = 'admin@ayena.in'
# # password = '1'

# # # Initialize Odoo connection
# # common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
# # uid = common.authenticate(db, username, password, {})
# # models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# # def safe_extract_id(m2o_value):
# #     """Safely extract integer ID from Many2one field."""
# #     if not m2o_value or m2o_value == [False, False]:
# #         return False
# #     if isinstance(m2o_value, list) and len(m2o_value) >= 1:
# #         id_val = m2o_value[0]
# #         if isinstance(id_val, int):
# #             return id_val
# #     return False

# # @router.get("/{sales_order}/{cabinet_position}")
# # async def get_bom_items(sales_order: str, cabinet_position: str):
# #     try:
# #         bom_data = fetch_full_bom_data(sales_order, cabinet_position)
# #         return JSONResponse(content=bom_data)
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# # def fetch_full_bom_data(sales_order: str, cabinet_position: str):
# #     # Fetch sale.order.line items
# #     sale_lines = models.execute_kw(
# #         db, uid, password,
# #         'sale.order.line', 'search_read',
# #         [[('order_id.name', '=', sales_order), ('x_studio_cabinet_position', '=', cabinet_position)]],
# #         {'fields': ['id', 'name', 'product_id', 'x_studio_cabinet_position', 'product_uom_qty', 'product_uom']}
# #     )

# #     if not sale_lines:
# #         raise HTTPException(status_code=404, detail="No BOM items found.")

# #     def explode_bom(product_id, product_tmpl_id, quantity=1.0, depth=0, max_depth=10, visited_boms=None):
# #         """
# #         Recursively explode BOM to get all components.
# #         visited_boms: set of bom_id to prevent infinite loops
# #         """
# #         if visited_boms is None:
# #             visited_boms = set()
            
# #         if depth > max_depth:
# #             print(f"Max recursion depth {max_depth} reached")
# #             return []
            
# #         # Find applicable BOM
# #         domain = [('product_tmpl_id', '=', product_tmpl_id)]
# #         if product_id:
# #             domain = ['|', ('product_id', '=', product_id)] + domain

# #         boms = models.execute_kw(
# #             db, uid, password,
# #             'mrp.bom', 'search_read',
# #             [domain],
# #             {'fields': ['id', 'product_id', 'product_tmpl_id', 'product_qty', 'product_uom_id'], 'limit': 1}
# #         )

# #         if not boms:
# #             # No BOM found - this is a leaf component
# #             return []
        
# #         bom = boms[0]
# #         bom_id = bom['id']
        
# #         # Check for cycles
# #         if bom_id in visited_boms:
# #             print(f"Cycle detected: BOM {bom_id} already visited")
# #             return []
            
# #         visited_boms.add(bom_id)
# #         print(f"Depth {depth}: Processing BOM {bom_id} for product_tmpl_id {product_tmpl_id}")

# #         # Fetch BOM lines (the actual components)
# #         bom_lines = models.execute_kw(
# #             db, uid, password,
# #             'mrp.bom.line', 'search_read',
# #             [[('bom_id', '=', bom_id)]],
# #             {'fields': ['id', 'product_id', 'product_qty', 'product_uom_id', 'bom_id']}
# #         )

# #         result = []
# #         for line in bom_lines:
# #             line_product_id = safe_extract_id(line.get('product_id'))
# #             line_qty = line.get('product_qty', 0)
            
# #             # Get product template for this component
# #             if line_product_id:
# #                 product = models.execute_kw(
# #                     db, uid, password,
# #                     'product.product', 'read',
# #                     [[line_product_id]],
# #                     {'fields': ['product_tmpl_id', 'name']}
# #                 )
                
# #                 if product:
# #                     line_product_tmpl_id = safe_extract_id(product[0].get('product_tmpl_id'))
                    
# #                     component = {
# #                         'product_name': product[0].get('name'),
# #                         'depth': depth,
# #                         'children': []
# #                     }
                    
# #                     # Recursively explode if this component has its own BOM
# #                     child_components = explode_bom(
# #                         line_product_id, 
# #                         line_product_tmpl_id, 
# #                         line_qty * quantity,
# #                         depth + 1, 
# #                         max_depth,
# #                         visited_boms.copy()  # Pass a copy to allow reuse in other branches
# #                     )
                    
# #                     if child_components:
# #                         component['children'] = child_components
                    
# #                     result.append(component)
        
# #         return result

# #     # Process each sale order line
# #     processed_items = []
# #     for line in sale_lines:
# #         product_id = safe_extract_id(line.get('product_id'))
# #         quantity = line.get('product_uom_qty', 1.0)
        
# #         if product_id:
# #             # Get product template
# #             product = models.execute_kw(
# #                 db, uid, password,
# #                 'product.product', 'read',
# #                 [[product_id]],
# #                 {'fields': ['product_tmpl_id', 'name']}
# #             )
            
# #             if product:
# #                 product_tmpl_id = safe_extract_id(product[0].get('product_tmpl_id'))
                
# #                 item = {
# #                     'product_name': product[0].get('name'),
# #                     'cabinet_position': line.get('x_studio_cabinet_position'),
# #                     'children': explode_bom(product_id, product_tmpl_id, quantity)
# #                 }
                
# #                 processed_items.append(item)
    
# #     return processed_items


# from fastapi import APIRouter, HTTPException
# from fastapi.responses import JSONResponse
# import xmlrpc.client

# router = APIRouter(prefix="/dashboard/bom", tags=["BOM"])

# # Odoo connection settings
# url = 'https://modula12.odoo.com'
# db = 'modula12'
# username = 'admin@ayena.in'
# password = '1'

# # Initialize Odoo connection
# common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
# uid = common.authenticate(db, username, password, {})
# models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# def safe_extract_id(m2o_value):
#     """Safely extract integer ID from Many2one field."""
#     if not m2o_value or m2o_value == [False, False]:
#         return False
#     if isinstance(m2o_value, list) and len(m2o_value) >= 1:
#         id_val = m2o_value[0]
#         if isinstance(id_val, int):
#             return id_val
#     return False

# def extract_product_name(product_field):
#     """Extract clean product name from Odoo Many2one field [id, name]."""
#     if not product_field or product_field == [False, False]:
#         return "Unknown Product"
#     if isinstance(product_field, list) and len(product_field) >= 2:
#         return product_field[1]  # The name is at index 1
#     return "Unknown Product"

# @router.get("/{sales_order}/{cabinet_position}")
# async def get_bom_items(sales_order: str, cabinet_position: str):
#     try:
#         bom_data = fetch_full_bom_data(sales_order, cabinet_position)
#         return JSONResponse(content=bom_data)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# def fetch_full_bom_data(sales_order: str, cabinet_position: str):
#     # Fetch sale.order.line items
#     sale_lines = models.execute_kw(
#         db, uid, password,
#         'sale.order.line', 'search_read',
#         [[('order_id.name', '=', sales_order), ('x_studio_cabinet_position', '=', cabinet_position)]],
#         {'fields': ['id', 'name', 'product_id', 'x_studio_cabinet_position', 'product_uom_qty', 'product_uom']}
#     )

#     if not sale_lines:
#         raise HTTPException(status_code=404, detail="No BOM items found.")

#     def explode_bom(product_id, product_tmpl_id, quantity=1.0, depth=0, max_depth=10, visited_boms=None):
#         """
#         Recursively explode BOM to get all components.
#         visited_boms: set of bom_id to prevent infinite loops
#         """
#         if visited_boms is None:
#             visited_boms = set()
            
#         if depth > max_depth:
#             print(f"Max recursion depth {max_depth} reached")
#             return []
            
#         # Find applicable BOM
#         domain = [('product_tmpl_id', '=', product_tmpl_id)]
#         if product_id:
#             domain = ['|', ('product_id', '=', product_id)] + domain

#         boms = models.execute_kw(
#             db, uid, password,
#             'mrp.bom', 'search_read',
#             [domain],
#             {'fields': ['id', 'product_id', 'product_tmpl_id', 'product_qty', 'product_uom_id'], 'limit': 1}
#         )

#         if not boms:
#             # No BOM found - this is a leaf component
#             return []
        
#         bom = boms[0]
#         bom_id = bom['id']
        
#         # Check for cycles
#         if bom_id in visited_boms:
#             print(f"Cycle detected: BOM {bom_id} already visited")
#             return []
            
#         visited_boms.add(bom_id)
#         print(f"Depth {depth}: Processing BOM {bom_id} for product_tmpl_id {product_tmpl_id}")

#         # Fetch BOM lines (the actual components)
#         bom_lines = models.execute_kw(
#             db, uid, password,
#             'mrp.bom.line', 'search_read',
#             [[('bom_id', '=', bom_id)]],
#             {'fields': ['id', 'product_id', 'product_qty', 'product_uom_id', 'bom_id']}
#         )

#         result = []
#         for line in bom_lines:
#             line_product_id = safe_extract_id(line.get('product_id'))
#             line_qty = line.get('product_qty', 0)
            
#             # Get product name - extract clean name from Many2one field
#             product_name = extract_product_name(line.get('product_id'))
            
#             # Get product template for this component
#             if line_product_id:
#                 product = models.execute_kw(
#                     db, uid, password,
#                     'product.product', 'read',
#                     [[line_product_id]],
#                     {'fields': ['product_tmpl_id']}
#                 )
                
#                 if product:
#                     line_product_tmpl_id = safe_extract_id(product[0].get('product_tmpl_id'))
                    
#                     component = {
#                         'product_name': product_name,
#                         'depth': depth,
#                         'children': []
#                     }
                    
#                     # Recursively explode if this component has its own BOM
#                     child_components = explode_bom(
#                         line_product_id, 
#                         line_product_tmpl_id, 
#                         line_qty * quantity,
#                         depth + 1, 
#                         max_depth,
#                         visited_boms.copy()  # Pass a copy to allow reuse in other branches
#                     )
                    
#                     if child_components:
#                         component['children'] = child_components
                    
#                     result.append(component)
        
#         return result

#     # Process each sale order line
#     processed_items = []
#     for line in sale_lines:
#         product_id = safe_extract_id(line.get('product_id'))
#         quantity = line.get('product_uom_qty', 1.0)
        
#         # Extract clean product name from Many2one field
#         product_name = extract_product_name(line.get('product_id'))
        
#         if product_id:
#             # Get product template
#             product = models.execute_kw(
#                 db, uid, password,
#                 'product.product', 'read',
#                 [[product_id]],
#                 {'fields': ['product_tmpl_id']}
#             )
            
#             if product:
#                 product_tmpl_id = safe_extract_id(product[0].get('product_tmpl_id'))
                
#                 item = {
#                     'sales_order': sales_order,
#                     'product_name': product_name,
#                     'cabinet_position': line.get('x_studio_cabinet_position'),
#                     'children': explode_bom(product_id, product_tmpl_id, quantity)
#                 }
                
#                 processed_items.append(item)
    
#     return processed_items


from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.requisite_schema import (
    BOMItemResponse, 
    SiteRequisiteSubmit, 
    SODetailResponse
)
from app.services.odoo_service import OdooService
from app.services.requisite_service import RequisiteService

router = APIRouter(prefix="/dashboard/bom", tags=["BOM"])

@router.get("/{sales_order}/{cabinet_position}", response_model=List[BOMItemResponse])
async def get_bom_items(sales_order: str, cabinet_position: str):
    """
    Fetch complete BOM hierarchy from Odoo in a single request
    """
    try:
        bom_data = OdooService.fetch_full_bom_data(sales_order, cabinet_position)
        return bom_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching BOM: {str(e)}")

@router.post("/submit", response_model=SODetailResponse)
async def submit_site_requisite(
    data: SiteRequisiteSubmit,
    db: Session = Depends(get_db)
):
    """
    Submit site requisite with bucket items
    """
    try:
        result = RequisiteService.submit_site_requisite(db, data)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting requisite: {str(e)}")

@router.get("/history", response_model=List[SODetailResponse])
async def get_requisite_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get all site requisite history
    """
    try:
        history = RequisiteService.get_history(db, limit, offset)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@router.get("/history/{sales_order}", response_model=SODetailResponse)
async def get_requisite_by_sales_order(
    sales_order: str,
    db: Session = Depends(get_db)
):
    """
    Get requisite history for specific sales order
    """
    try:
        result = RequisiteService.get_history_by_sales_order(db, sales_order)
        if not result:
            raise HTTPException(status_code=404, detail="Sales order not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.patch("/status/{so_id}")
async def update_requisite_status(
    so_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update site requisite status
    """
    if status not in ["pending", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    try:
        result = RequisiteService.update_status(db, so_id, status)
        if not result:
            raise HTTPException(status_code=404, detail="SO not found")
        return {"message": "Status updated successfully", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
