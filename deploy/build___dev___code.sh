rm .dockerignore \
; rm Dockerfile \
; cp ./deploy/.dockerignore_top .dockerignore \
&& cp ./deploy/Dockerfile_dev_top Dockerfile \
&& docker build --platform linux/amd64 -t spout/spout-dev . \
&& docker tag spout/spout-dev:latest 904233102066.dkr.ecr.ap-southeast-1.amazonaws.com/spout/spout-dev:latest \
&& docker push 904233102066.dkr.ecr.ap-southeast-1.amazonaws.com/spout/spout-dev:latest \
&& rm .dockerignore \
&& rm Dockerfile
