STACK_NAME=$(ENV)-serverless-video-pipeline
THIS_DIR:=$(shell pwd)
MAIN_TEMPLATE_NAME = serverless-video-pipeline.yml
SOURCE_TEMPLATE_PATH = cloudformation/$(MAIN_TEMPLATE_NAME)
GENERATED_TEMPLATE_ABSOLUTE_PATH = $(THIS_DIR)/dist/$(SOURCE_TEMPLATE_PATH)

CHALICE_PROJECT_DIR = $(THIS_DIR)/api
CHALICE_PACKAGE_DIR = $(THIS_DIR)/dist/chalice-packaged
CHALICE_PACKAGED_SAM_TEMPLATE_PATH = $(CHALICE_PACKAGE_DIR)/sam.json
PARAMETRIZED_SAM_TEMPLATE_PATH = $(CHALICE_PACKAGE_DIR)/sam-parametrized.json
GENERATED_SAM_TEMPLATE_ABSOLUTE_PATH = $(THIS_DIR)/dist/cloudformation/sam.yml

BUCKET_NAME = serverless-video-pipeline-`aws sts get-caller-identity --output text --query 'Account'`-`aws configure get region`
TRANSCODER_BUCKET=`aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query "Stacks[0].Outputs[?OutputKey=='TranscoderBucket'].OutputValue" --output text`

# Check if variable has been defined, otherwise print custom error message
check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
      $(error Undefined $1$(if $2, ($2))))

check-bucket:
	@aws s3api head-bucket --bucket $(BUCKET_NAME) &> /dev/null || aws s3 mb s3://$(BUCKET_NAME)

check-env-defined:
	$(call check_defined, ENV, Ex: make $(MAKECMDGOALS) ENV=stage)

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf $(CHALICE_PACKAGE_DIR) || true

package-chalice: check-env-defined clean
	chalice --project-dir $(CHALICE_PROJECT_DIR) package $(CHALICE_PACKAGE_DIR) --stage=$(ENV)

package-cf-with-api: package-chalice check-bucket
	python ./scripts/parametrize_sam_template.py $(CHALICE_PACKAGED_SAM_TEMPLATE_PATH) $(PARAMETRIZED_SAM_TEMPLATE_PATH)
	aws cloudformation package --template-file $(PARAMETRIZED_SAM_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/$(SOURCE_TEMPLATE_PATH) --output-template-file $(GENERATED_SAM_TEMPLATE_ABSOLUTE_PATH)
	aws cloudformation package --template-file $(SOURCE_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/$(SOURCE_TEMPLATE_PATH) --output-template-file $(GENERATED_TEMPLATE_ABSOLUTE_PATH)
	python ./scripts/merge_sam_template.py $(GENERATED_TEMPLATE_ABSOLUTE_PATH) $(GENERATED_SAM_TEMPLATE_ABSOLUTE_PATH)

package-cf-without-api: check-bucket
	aws cloudformation package --template-file $(SOURCE_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/$(SOURCE_TEMPLATE_PATH) --output-template-file $(GENERATED_TEMPLATE_ABSOLUTE_PATH)

deploy: check-env-defined package-cf-with-api
	aws cloudformation deploy --template-file $(GENERATED_TEMPLATE_ABSOLUTE_PATH) --stack-name $(STACK_NAME) --capabilities CAPABILITY_IAM --parameter-overrides Environment=$(ENV)

sync-watermarks: check-env-defined
	aws s3 sync --delete assets/watermarks s3://$(TRANSCODER_BUCKET)/watermarks

first-deploy: deploy sync-watermarks
