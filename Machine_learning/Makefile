CC=icpc
ELF=data

FLAGS= -qopenmp
FLAGS+= -mkl
FLAGS+= -std=c++11
OPT_REPORT_FLAGS= -qopt-report -qopt-report-phase=loop,vec

SOURCE_PATH= .

TARGET_MODEL= Data_parallel
OBJS = learner.o main.o

FILES_PATH = $(SOURCE_PATH)/$(TARGET_MODEL)

all: ${ELF}

${ELF}: ${OBJS}
	$(CC) $(FLAGS) $(OBJS) -o ${ELF}

learner.o : ${FILES_PATH}/learner.cpp
	$(CC) $(FLAGS) $(OPT_REPORT_FLAGS) -c ${FILES_PATH}/learner.cpp

main.o : ${FILES_PATH}/main.cpp
	$(CC) $(FLAGS) $(OPT_REPORT_FLAGS) -c ${FILES_PATH}/main.cpp

clean:
	rm ./*.o data *.optrpt
