APP_PROD = cfa-api-prod
COMPOSE_FILE_PROD = docker-compose.yaml
DATABASE_NAME_PROD = cfa-db-prod

APP_DEV = cfa-api-dev
COMPOSE_FILE_DEV = docker-compose.dev.yaml
DATABASE_NAME_DEV = cfa-db-dev

APP_TEST = cfa-api-staging
COMPOSE_FILE_TEST = docker-compose.staging.yaml
DATABASE_NAME_TEST = cfa-db-staging


start: 
	docker compose up --build
start-server: 
	docker compose up --build $(APP_PROD)
build:
	docker compose build
up:
	docker compose up -d
shell:
	docker compose exec $(APP_PROD) python manage.py shell
shellplus:
	docker compose exec $(APP_PROD) python manage.py shell_plus
down:
	docker compose down
migrate:
	docker compose run $(APP_PROD) python manage.py migrate --fake
migrations:
	docker compose run $(APP_PROD) python manage.py makemigrations
migrationsmerge:
	docker compose run $(APP_PROD) python manage.py makemigrations --merge
test:
	docker compose run $(APP_PROD) python manage.py test $($(APP_PROD))
db:
	docker compose exec db psql --username=$(USERNAME) --dbname=$(DBNAME)
superuser:
	docker compose run $(APP_PROD) python manage.py createsuperuser
startapp:
	docker compose exec $(APP_PROD) python manage.py startapp $(APP_PROD)
update_countries_plus:
	docker compose run $(APP_PROD) python manage.py update_countries_plus
create_permissions:
	docker compose run $(APP_PROD) python manage.py create_permissions
create_roles:
	docker compose run $(APP_PROD) python manage.py create_roles
create_features_plan:
	docker compose run $(APP_PROD) python manage.py create_features_plan
create_activity:
	docker compose run $(APP_PROD) python manage.py create_activity
create_super_user:
	docker compose run $(APP_PROD) python manage.py create_super_user
super_user: create_permissions create_roles create_activity create_super_user
restart: build up
prod: build up


# Development stage
dev: 
	docker-compose -f $(COMPOSE_FILE_DEV) up --build $(APP_DEV)
dev-build: 
	docker-compose -f $(COMPOSE_FILE_DEV) build
dev-up: 

	docker-compose -f $(COMPOSE_FILE_DEV) up -d
hard-down:
	docker-compose -f $(COMPOSE_FILE_DEV) down --remove-orphans && docker volume prune -f
dev-down:
	docker-compose -f $(COMPOSE_FILE_DEV) down
re-dev: dev-build dev-up
develop: dev-build dev-up
dev-superuser:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py createsuperuser
dev_update_countries_plus:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py update_countries_plus
dev_create_permissions:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py create_permissions
dev_create_roles:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py create_roles
dev_create_features_plan:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py create_features_plan
dev_create_activity:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py create_activity
dev_migrate:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py migrate --fake 
dev_migrations:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py makemigrations
dev_migrationsmerge:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py makemigrations --merge
dev_create_super_user:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py create_super_user
dev_super_user: dev_create_permissions dev_create_roles dev_create_activity dev_create_super_user
dev_shell:
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py shell
dev_create_app:
	@if [ -z "$(APP_NAME)" ]; then \
		echo "Error: APP_NAME is required. Usage: make dev_create_app APP_NAME=<app_name>"; \
		exit 1; \
	fi
	docker-compose -f $(COMPOSE_FILE_DEV) run $(APP_DEV) python manage.py startapp $(APP_NAME)


# Testing/Staging stage
staging-run: 
	docker compose -f $(COMPOSE_FILE_TEST) up --build
staging-build: 
	docker compose -f $(COMPOSE_FILE_TEST) build
staging-up: 
	docker compose -f $(COMPOSE_FILE_TEST) up -d
staging-down:
	docker compose -f $(COMPOSE_FILE_TEST) down
re-staging: staging-build staging-up
staging: staging-build staging-up
staging-superuser:
	docker compose -f $(COMPOSE_FILE_TEST) run $(APP_TEST) python manage.py createsuperuser
staging_update_countries_plus:
	docker compose -f $(COMPOSE_FILE_TEST) run $(APP_TEST) python manage.py update_countries_plus
staging_create_permissions:
	docker compose -f $(COMPOSE_FILE_TEST) run $(APP_TEST) python manage.py create_permissions
staging_create_roles:
	docker compose -f $(COMPOSE_FILE_TEST) run $(APP_TEST) python manage.py create_roles
staging_create_features_plan:
	docker compose -f $(COMPOSE_FILE_TEST) run $(APP_TEST) python manage.py create_features_plan
staging_create_activity:
	docker compose -f $(COMPOSE_FILE_TEST) run $(APP_TEST) python manage.py create_activity
staging_create_super_user:
	docker compose -f $(COMPOSE_FILE_TEST) run $(APP_TEST) python manage.py create_super_user
staging_migrate:
	docker-compose -f $(COMPOSE_FILE_TEST) run $(APP_TEST) python manage.py migrate --fake
staging_migrations:
	docker-compose -f $(COMPOSE_FILE_TEST) run $(APP_TEST) python manage.py makemigrations
staging_migrationsmerge:
	docker-compose -f $(COMPOSE_FILE_TEST) run $(APP_TEST) python manage.py makemigrations --merge

staging_super_user: staging_create_permissions staging_create_roles staging_create_activity staging_create_super_user

