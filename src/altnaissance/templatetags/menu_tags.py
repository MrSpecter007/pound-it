from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def active_class(context, pattern):
    request = context.get('request')
    if not request:
        return ''
    
    current_path = request.path.rstrip('/')  # enlève le slash final
    pattern = pattern.rstrip('/')
    
    # ✅ Vérifie si l'URL commence par le pattern EXACT, pas juste contient
    if current_path == pattern or current_path.startswith(pattern + '/'):
        return 'current'
    
    return ''
