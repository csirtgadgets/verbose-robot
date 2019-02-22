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

docker-test:
	@bash docker/run_test.sh

vagrant:
	@bash helpers/test_ubuntu16.sh
