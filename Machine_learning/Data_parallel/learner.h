#ifndef __LEARNER_H__
#define __LEARNER_H__

#include <sys/time.h>
#include <math.h>

#define NUM_LAYER 7

#define INPUT_SIZE 784
#define HIDDEN_SIZE 800, 600, 400, 200, 100
#define OUTPUT_SIZE 10

#define LEARNING_RATE 0.01	// need to set


/******************************************************
 *
 * num_layer : number of layers (include input, output layer)
 *
 * layer_size : array for each layers size
 *
 * value : each node's output
 *
 ******************************************************/

/*				To Timer			*/
#define START_T     gettimeofday(&start_t, NULL);
#define END_T(x)    gettimeofday(&end_t, NULL);\
                    timersub(&end_t, &start_t, &exec_t);\
                    timeradd(&exec_t, &sum_t[x], &sum_t[x]);
extern timeval start_t, end_t, sum_t[10], exec_t;

class Net{
private:
    int nThread;
    int num_layer;
    int mini_batch_size;

    int *ac_weights;
    int *ac_neurals;

    int *layer_size;
    double *value;
    double *weight;
    double *bias;
    double *error;

public:
    Net(int *layer_size, int num_layer, int mini_batch_size, int epoch, int num_thread);
    ~Net();

    void train(double input[][INPUT_SIZE], double desired[][OUTPUT_SIZE], int num_data);
    double *test(double *input);

private:
    void initializer();

    double sigmoid(double num);

    void feedforward(double *input, int data_num);
    void back_pass(double *desired, double *error, int data_num);
    void backpropagation(double learning_rate, int num_data);
};


#endif /* __LEARNER_H__ */
