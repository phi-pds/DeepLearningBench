#TARGETS=hello hello2 
TARGETS=hello Machine_learning

all: $(addprefix all-,$(TARGETS))
clean: $(addprefix clean-,$(TARGETS))

.PHONY: always

all-hello: always
	$(MAKE) -C hello all

clean-hello: always
	$(MAKE) -C hello clean

all-Machine_learning: always
	$(MAKE) -C Machine_learning all

clean-Machine_learning: always
	$(MAKE) -C Machine_learning clean
