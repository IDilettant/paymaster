compose:
	docker-compose up -d

compose-production:
	docker-compose --file docker-compose.yml run paymaster

compose-build:
	docker-compose build

compose-logs:
	docker-compose logs -f

compose-down:
	docker-compose down || true

compose-stop:
	docker-compose stop || true

compose-restart:
	docker-compose restart
