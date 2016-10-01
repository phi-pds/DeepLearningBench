#TARGETS=hello hello2 
TARGETS=hello

all: $(addprefix all-,$(TARGETS))
clean: $(addprefix clean-,$(TARGETS))

.PHONY: always

all-hello: always
	$(MAKE) -C hello all

clean-hello: always
	$(MAKE) -C hello clean
