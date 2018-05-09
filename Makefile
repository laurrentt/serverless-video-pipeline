STACK_NAME=$(ENV)-serverless-video-pipeline
THIS_DIR:=$(shell pwd)
MAIN_TEMPLATE_NAME = serverless-video-pipeline.yml
SOURCE_TEMPLATE_PATH = cloudformation/$(MAIN_TEMPLATE_NAME)
GENERATED_TEMPLATE_ABSOLUTE_PATH = $(THIS_DIR)/dist/$(SOURCE_TEMPLATE_PATH)

BUCKET_NAME = serverless-video-pipeline-`aws sts get-caller-identity --output text --query 'Account'`-`aws configure get region`

# Check if variable has been defined, otherwise print custom error message
check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
      $(error Undefined $1$(if $2, ($2))))

check-bucket:
	@aws s3api head-bucket --bucket $(BUCKET_NAME) &> /dev/null || aws s3 mb s3://$(BUCKET_NAME)

package: check-bucket
	aws cloudformation package --template-file $(SOURCE_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/$(SOURCE_TEMPLATE_PATH) --output-template-file $(GENERATED_TEMPLATE_ABSOLUTE_PATH)

deploy: package
	$(call check_defined, ENV, Ex: make deploy ENV=stage)
	aws cloudformation deploy --template-file $(GENERATED_TEMPLATE_ABSOLUTE_PATH) --stack-name $(STACK_NAME) --capabilities CAPABILITY_IAM --parameter-overrides Environment=$(ENV)
