.PHONY: clean test sdist all docker docker-test vagrant test-es

all: test sdist

clean:
	rm -rf `find . | grep \.pyc`
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

test:
	@python setup.py test 

dist:
	@python setup.py sdist

docker:
	@bash docker_build.sh

docker-test: docker
	@bash docker/run_test.sh

docker-run:
	@bash docker/run.sh

docker-test-es:
	@bash docker/run_test_es.sh

vagrant:
	@bash helpers/test_ubuntu16.sh
