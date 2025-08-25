from accounts.models import Organisation

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from accounts.models import Organisation, Role, Services
import logging

User = get_user_model()
logger = logging.getLogger(__name__)



def ldap_user_populate(user, ldap_user):
    email = ldap_user.attrs.get("mail", [None])[0]
    if email:
        domain = email.split("@")[-1]
        org, _ = Organisation.objects.get_or_create(domain=domain, defaults={"name": domain})
        user.organisation = org
        user.save()

def get_or_create_org_from_email(email, company_name=None):
    """
    Extract domain from email and create/get organization
    """
    if not email or "@" not in email:
        return None
    
    domain = email.split("@")[-1].lower()
    
    # Skip common public email providers
    public_domains = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
        'live.com', 'aol.com', 'icloud.com', 'protonmail.com'
    ]
    
    if domain in public_domains:
        logger.info(f"Skipping organization creation for public domain: {domain}")
        return None
    
    try:
        org, created = Organisation.objects.get_or_create(
            domain=domain,
            defaults={
                'name': company_name or domain.split('.')[0].title()
            }
        )
        if created:
            logger.info(f"Created organization: {org.name} for domain: {domain}")
        return org
    except Exception as e:
        logger.error(f"Error creating organization for domain {domain}: {str(e)}")
        return None

def create_sso_user(email, first_name="", last_name="", company_name=None, auth_provider="azure"):
    """
    Create or update user from SSO data
    """
    if not email:
        raise ValidationError("Email is required")
    
    # Get or create organization
    org = get_or_create_org_from_email(email, company_name)
    
    # Create or update user
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'organisation': org,
            'is_active': True,
        }
    )
    
    # Update existing user if needed
    if not created:
        updated = False
        if user.first_name != first_name and first_name:
            user.first_name = first_name
            updated = True
        if user.last_name != last_name and last_name:
            user.last_name = last_name
            updated = True
        if user.organisation != org and org is not None:
            user.organisation = org
            updated = True
        if not user.is_active:
            user.is_active = True
            updated = True
            
        if updated:
            user.save()
            logger.info(f"Updated user: {email}")
    else:
        logger.info(f"Created new user: {email}")
    
    return user, created

def assign_default_role_to_user(user, role_name="User"):
    """
    Assign a default role to user if Role model is being used
    """
    try:
        role, _ = Role.objects.get_or_create(name=role_name)
        # If you have a ManyToMany relationship between User and Role
        # user.roles.add(role)
        # user.save()
        return role
    except Exception as e:
        logger.error(f"Error assigning role to user {user.email}: {str(e)}")
        return None

def get_user_permissions(user):
    """
    Get user permissions based on organization and roles
    """
    permissions = {
        'can_access_admin': user.is_staff or user.is_superuser,
        'can_manage_users': user.is_staff,
        'organization': user.organisation.name if user.organisation else None,
        'organization_id': str(user.organisation.id) if user.organisation else None,
    }
    
    # Add role-based permissions if using Role model
    # user_roles = user.roles.all()  # Assuming ManyToMany relationship
    # permissions['roles'] = [role.name for role in user_roles]
    
    return permissions