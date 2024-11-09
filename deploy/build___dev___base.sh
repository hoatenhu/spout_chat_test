cp ./deploy/.dockerignore_base .dockerignore \
&& cp ./deploy/Dockerfile_base Dockerfile \
&& docker build --platform linux/amd64 -t spout/spout-dev-base .  \
&& docker tag spout/spout-dev-base:latest 904233102066.dkr.ecr.ap-southeast-1.amazonaws.com/spout/spout-dev-base:latest       \
&& docker push 904233102066.dkr.ecr.ap-southeast-1.amazonaws.com/spout/spout-dev-base:latest \
&& rm Dockerfile \
&& rm .dockerignore
