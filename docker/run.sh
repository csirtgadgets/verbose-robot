#!/bin/bash

C=$(docker run -it -d -p 5000:5000 --name verbose-robot csirtgadgets/verbose-robot)

echo "Getting a shell into the container..."
docker exec -it $C /bin/bash