#include "learner.h"
#include "mkl.h"
#include <omp.h>

#define TOTAL_NEURALS()     AC_NEURALS(this->num_layer-1)
#define TOTAL_WEIGHTS()     AC_WEIGHTS(this->num_layer-2)

#define AC_NEURALS(L)       (0 > L ? 0 : this->ac_neurals[L])
#define AC_WEIGHTS(L)       (0 > L ? 0 : this->ac_weights[L])

#define BIAS(i, j)          (this->bias[AC_NEURALS(i-1) + j])
#define VALUE(i, j, k)      (this->value[i*TOTAL_NEURALS() + AC_NEURALS(j-1) + k])
#define ERROR(i, j, k)      (this->error[i*TOTAL_NEURALS() + AC_NEURALS(j-1) + k])
#define WEIGHT(i, j, k)     (this->weight[AC_WEIGHTS(i-1) + j*layer_size[i+1] + k])

// constructor
Net::Net(int *layer_size, int num_layer, int mini_batch_size, int epoch, int num_thread)
{
    int i, j, k;
    int before_ac_weights = 0;
    int before_ac_neurals = 0;

    nThread = num_thread;

    // write on class vars
    this->num_layer = num_layer;
    this->mini_batch_size = mini_batch_size;

    // layer size
    this->layer_size = new int[num_layer];
    this->ac_neurals = new int[num_layer];
    this->ac_weights = new int[num_layer];

    for(i=0; i<num_layer; i++) {
        this->layer_size[i] = layer_size[i];
        this->ac_neurals[i] = layer_size[i] + before_ac_neurals;
        before_ac_neurals = this->ac_neurals[i];

        if (i == num_layer-1)
            continue;

        this->ac_weights[i] = layer_size[i]*layer_size[i+1] + before_ac_weights;
        before_ac_weights = this->ac_weights[i];

    }

    this->value = new double[mini_batch_size * TOTAL_NEURALS()];
    this->error = new double[mini_batch_size * TOTAL_NEURALS()];
    this->bias = new double[TOTAL_NEURALS()];
    weight = new double[TOTAL_WEIGHTS()];

    // input random initial weights & biases(-1 ~ 1)
    for(i=0; i<num_layer-1; i++)
        for(j=0; j<layer_size[i]; j++)
            for(k=0; k<layer_size[i+1]; k++)
                WEIGHT(i, j, k) = (double)rand()/(RAND_MAX/2)-1;

    for(i=1; i<num_layer; i++)
        for(j=0; j<layer_size[i]; j++)
            BIAS(i, j) = 0;
}

Net::~Net()
{
    int i, j;

    delete[] weight;
    delete[] this->bias;
    delete[] error;
    delete[] value;
    delete[] layer_size;
}

void Net::train(double input[][INPUT_SIZE], double desired[][OUTPUT_SIZE], int num_data)
{
    int i;
    START_T
    initializer();
    END_T(0)

    START_T
#pragma omp parallel for num_threads(num_data)
    for(i=0; i<num_data; i++){
        feedforward(input[i], i);
        back_pass(desired[i], &ERROR(i, 0, 0), i);
    }
    END_T(1)

    START_T
    backpropagation(LEARNING_RATE, num_data);
    END_T(2)
}

double* Net::test(double *input)
{
    initializer();
    feedforward(input, 0);
    return &VALUE(0, num_layer-1, 0);
}

void Net::initializer()
{
    int i, j, k;
#pragma omp parallel for num_threads(nThread)
    for(k=0; k<mini_batch_size; k++)
        for(i=1; i<num_layer; i++)
            for(j=0; j<layer_size[i]; j++)
                ERROR(k, i, j) = 0;
}

double Net::sigmoid(double num){
    return 1/(1 + exp(-num));
}

void Net::feedforward(double* input, int data_num){
    int i, j, k;
    for(i=0; i<layer_size[0]; i++)
        VALUE(data_num, 0, i) = input[i];

#if 1
    for (i = 0; i <num_layer-1; i++) {
        cblas_dgemv(
                CblasRowMajor,
                CblasTrans,
                layer_size[i],
                layer_size[i+1],
                1.0,
                (const double *) &WEIGHT(i, 0, 0),
                layer_size[i+1],
                (const double *) &VALUE(data_num, i, 0),
                1,
                0.0,
                (double *) &VALUE(data_num, i+1, 0),
                1
                );
        cblas_daxpy(layer_size[i+1], 1.0,  (double *)&BIAS(i+1, 0), 1, (double *) &VALUE(data_num, i+1, 0), 1.0);

        for (j = 0; j < layer_size[i+1]; j++) {
            VALUE(data_num, i+1, j) = sigmoid(VALUE(data_num, i+1, j));
        }
    }
#else
    for(i=0; i<num_layer-1; i++) {
        for(k=0; k<layer_size[i+1]; k++){
            double sum = 0;
            for(j=0; j<layer_size[i]; j++)
                sum += WEIGHT(i, j, k)*VALUE(data_num, i, j);
            VALUE(data_num, i+1, k) = sigmoid(sum + BIAS(i+1, k));
        }
    }
#endif
}

void Net::back_pass(double *desired, double *error, int data_num)
{
    int i, j, k;

    for(i=0; i<layer_size[num_layer-1]; i++)
        ERROR(data_num, num_layer-1, i) = VALUE(data_num, num_layer-1, i) - desired[i];
    for(i=num_layer-2; i>0; i--)
        for(j=0; j<layer_size[i]; j++)
            for(k=0; k<layer_size[i+1]; k++)
                ERROR(data_num, i, j) += ERROR(data_num, i+1, k)*WEIGHT(i, j, k);
}

void Net::backpropagation(double learning_rate, int num_data)
{
    int i, j, k, no_loop=0;

#pragma omp parallel for num_threads(nThread)
    for(i=1; i<num_layer-1; i++)
        no_loop += layer_size[i];

#pragma omp parallel for num_threads(nThread)
    for(i=0; i<no_loop; i++)
        for(j=1; j<num_data; j++){
            int sum_nu = 0, no_layer = 1;
            while(i >= sum_nu + layer_size[no_layer])
                sum_nu += layer_size[no_layer], no_layer++;

            ERROR(0, no_layer, i-sum_nu) += ERROR(j, no_layer, i-sum_nu);
        }

#pragma omp parallel for num_threads(nThread)
    for(i=0; i<no_loop; i++)
        for(j=1; j<num_data; j++){
            int sum_nu = 0, no_layer = 1;
            while(i >= sum_nu + layer_size[no_layer])
                sum_nu += layer_size[no_layer], no_layer++;

            ERROR(0, no_layer, i-sum_nu) /= num_data;
        }

    // update weight
    no_loop = 0;
#pragma omp parallel for num_threads(nThread)
    for(i=0; i<num_layer-1; i++)
        no_loop += layer_size[i]*layer_size[i+1];

#pragma omp parallel for num_threads(nThread)
    for(i=0; i<no_loop; i++){
        int sum_nu = 0, no_layer = 0;
        while(i >= sum_nu + layer_size[no_layer]*layer_size[no_layer+1])
            sum_nu += layer_size[no_layer]*layer_size[no_layer+1], no_layer++;

        int no_no = 0;
        while(i >= sum_nu + layer_size[no_layer+1])
            sum_nu += layer_size[no_layer+1], no_no++;

        WEIGHT(no_layer, no_no, i-sum_nu) -= ERROR(0, no_layer+1, i-sum_nu)
        * VALUE(num_data-1, no_layer+1, i-sum_nu)*(1-VALUE(num_data-1, no_layer+1, i-sum_nu))
        * VALUE(num_data-1, no_layer, no_no)
        * learning_rate;
    }

    // update bias
    no_loop = 0;
#pragma omp parallel for num_threads(nThread)
    for(i=1; i<num_layer-1; i++)
        no_loop += layer_size[i];

#pragma omp parallel for num_threads(nThread)
    for(i=0; i<no_loop; i++){
        int sum_nu = 0, no_layer = 1;
        while(i >= sum_nu + layer_size[no_layer])
            sum_nu += layer_size[no_layer], no_layer++;

        BIAS(no_layer, i-sum_nu) -= ERROR(0, no_layer+1, i-sum_nu)
        * VALUE(num_data-1, no_layer+1, i-sum_nu)*(1-VALUE(num_data-1, no_layer+1, i-sum_nu))
        * VALUE(num_data-1, no_layer, i-sum_nu)
        * learning_rate;
    }
}

