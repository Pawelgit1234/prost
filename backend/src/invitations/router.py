import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/invitations', tags=['invitations'])