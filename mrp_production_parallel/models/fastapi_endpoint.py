from typing import Annotated

from fastapi import APIRouter, Depends

from pydantic import BaseModel

from odoo import api, fields, models
from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("demo", "Demo Router")], 
        ondelete={"demo": "cascade"}
    )

    def _get_fastapi_routers(self):
        if self.app == "demo":
            return [demo_api_router]
        return super()._get_fastapi_routers()


demo_api_router = APIRouter()


class ProductionInfo(BaseModel):
    name: str
    type: str

@demo_api_router.get("/productions", response_model=list[ProductionInfo])
def get_productions(env: Annotated[Environment, Depends(odoo_env)]) -> list[ProductionInfo]:
    return [
        ProductionInfo(name=production.name, type=production.type)
        for production in env["mrp.production"].sudo().search([])
    ]

