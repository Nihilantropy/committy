all:
	./scripts/install-dev.sh

clean: 
	rm -rf venv

fclean: clean delete_config
	
re: fclean all
	
delete_config:
	rm ~/.local/bin/committy