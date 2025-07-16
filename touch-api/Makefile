# TODO: ADD DOCSTRING: https://dev.to/feldroy/autodocumenting-makefiles-175b
deploy:
	git stash
	git pull
	test -x ./deploy.sh || sudo chmod +x ./deploy.sh
	./deploy.sh