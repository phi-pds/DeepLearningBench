TARGETS=hello inception

all: $(addprefix all-,$(TARGETS))
clean: $(addprefix clean-,$(TARGETS))

.PHONY: always

all-hello: always
	$(MAKE) -C hello all

clean-hello: always
	$(MAKE) -C hello clean

all-inception: always
	$(MAKE) -C inception all

clean-inception: always
	$(MAKE) -C inception clean

