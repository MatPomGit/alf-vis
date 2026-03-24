class ResizeBilinearLayer CV_FINAL : public cv::dnn::Layer
{
public:
ResizeBilinearLayer(const cv::dnn::LayerParams &params) : Layer(params)
{
CV_Assert(!params.get<bool>("align_corners", false));
CV_Assert(!blobs.empty());
for (size_t i = 0; i < blobs.size(); ++i)
CV_Assert(blobs[i].type() == CV_32SC1);
// There are two cases of input blob: a single blob which contains output
// shape and two blobs with scaling factors.
if (blobs.size() == 1)
{
CV_Assert(blobs[0].total() == 2);
outHeight = blobs[0].at<int>(0, 0);
outWidth = blobs[0].at<int>(0, 1);
factorHeight = factorWidth = 0;
}
else
{
CV_Assert(blobs.size() == 2); CV_Assert(blobs[0].total() == 1); CV_Assert(blobs[1].total() == 1);
factorHeight = blobs[0].at<int>(0, 0);
factorWidth = blobs[1].at<int>(0, 0);
outHeight = outWidth = 0;
}
}
static cv::Ptr<cv::dnn::Layer> create(cv::dnn::LayerParams& params)
{
return cv::Ptr<cv::dnn::Layer>(new ResizeBilinearLayer(params));
}
virtual bool getMemoryShapes(const std::vector<std::vector<int> > &inputs,
const int,
std::vector<std::vector<int> > &outputs,
std::vector<std::vector<int> > &) const CV_OVERRIDE
{
std::vector<int> outShape(4);
outShape[0] = inputs[0][0]; // batch size
outShape[1] = inputs[0][1]; // number of channels
outShape[2] = outHeight != 0 ? outHeight : (inputs[0][2] * factorHeight);
outShape[3] = outWidth != 0 ? outWidth : (inputs[0][3] * factorWidth);
outputs.assign(1, outShape);
return false;
}
virtual void finalize(cv::InputArrayOfArrays, cv::OutputArrayOfArrays outputs_arr) CV_OVERRIDE
{
std::vector<cv::Mat> outputs;
outputs_arr.getMatVector(outputs);
if (!outWidth && !outHeight)
{
outHeight = outputs[0].size[2];
outWidth = outputs[0].size[3];
}
}
// This implementation is based on a reference implementation from
// https://github.com/tensorflow/tensorflow/blob/master/tensorflow/contrib/lite/kernels/internal/reference/reference_ops.h
virtual void forward(cv::InputArrayOfArrays inputs_arr,
cv::OutputArrayOfArrays outputs_arr,
cv::OutputArrayOfArrays internals_arr) CV_OVERRIDE
{
if (inputs_arr.depth() == CV_16S)
{
// In case of DNN_TARGET_OPENCL_FP16 target the following method
// converts data from FP16 to FP32 and calls this forward again.
forward_fallback(inputs_arr, outputs_arr, internals_arr);
return;
}
std::vector<cv::Mat> inputs, outputs;
inputs_arr.getMatVector(inputs);
outputs_arr.getMatVector(outputs);
cv::Mat& inp = inputs[0];
cv::Mat& out = outputs[0];
const float* inpData = (float*)inp.data;
float* outData = (float*)out.data;
const int batchSize = inp.size[0];
const int numChannels = inp.size[1];
const int inpHeight = inp.size[2];
const int inpWidth = inp.size[3];
float heightScale = static_cast<float>(inpHeight) / outHeight;
float widthScale = static_cast<float>(inpWidth) / outWidth;
for (int b = 0; b < batchSize; ++b)
{
for (int y = 0; y < outHeight; ++y)
{
float input_y = y * heightScale;
int y0 = static_cast<int>(std::floor(input_y));
int y1 = std::min(y0 + 1, inpHeight - 1);
for (int x = 0; x < outWidth; ++x)
{
float input_x = x * widthScale;
int x0 = static_cast<int>(std::floor(input_x));
int x1 = std::min(x0 + 1, inpWidth - 1);
for (int c = 0; c < numChannels; ++c)
{
float interpolation =
inpData[offset(inp.size, c, x0, y0, b)] * (1 - (input_y - y0)) * (1 - (input_x - x0)) +
inpData[offset(inp.size, c, x0, y1, b)] * (input_y - y0) * (1 - (input_x - x0)) +
inpData[offset(inp.size, c, x1, y0, b)] * (1 - (input_y - y0)) * (input_x - x0) +
inpData[offset(inp.size, c, x1, y1, b)] * (input_y - y0) * (input_x - x0);
outData[offset(out.size, c, x, y, b)] = interpolation;
}
}
}
}
}
private:
static inline int offset(const cv::MatSize& size, int c, int x, int y, int b)
{
return x + size[3] * (y + size[2] * (c + size[1] * b));
}
int outWidth, outHeight, factorWidth, factorHeight;
};