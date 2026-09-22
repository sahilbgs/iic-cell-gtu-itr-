"""
GTU-ITR R&D & IIC Portal - Principal Post Routes Package
Blueprint: posts  |  Prefix: /posts
"""
from flask import Blueprint

posts_bp = Blueprint('posts', __name__, url_prefix='/posts')

ALLOWED_UPLOAD_EXT = {'pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg'}


def _allowed_file(filename):
    """Check if file extension is allowed for uploads."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_UPLOAD_EXT


# Import submodules to register routes onto posts_bp
from routes.posts import crud, extraction, forms, exports, reports  # noqa: E402, F401
