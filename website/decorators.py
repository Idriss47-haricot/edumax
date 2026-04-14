from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def super_admin_required(view_func):
    """Vérifie que l'utilisateur est Super Admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'super_admin':
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('dashboard')
    return wrapper

def admin_ecole_required(view_func):
    """Vérifie que l'utilisateur est Admin École"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'admin_ecole':
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('dashboard')
    return wrapper

def enseignant_required(view_func):
    """Vérifie que l'utilisateur est Enseignant ou Admin École ou Super Admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role in ['enseignant', 'admin_ecole', 'super_admin']:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('dashboard')
    return wrapper

def etudiant_required(view_func):
    """Vérifie que l'utilisateur est Étudiant"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'etudiant':
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('dashboard')
    return wrapper

def ecole_admin_or_superadmin(view_func):
    """Vérifie que l'utilisateur est Admin de l'école concernée ou Super Admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.role == 'super_admin':
                return view_func(request, *args, **kwargs)
            if request.user.role == 'admin_ecole' and request.user.ecole_admin:
                # Vérifier si l'école dans l'URL correspond à celle de l'admin
                ecole_id = kwargs.get('ecole_id')
                if ecole_id and request.user.ecole_admin.id == int(ecole_id):
                    return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('dashboard')
    return wrapper