#include <vector>
#include <cmath> // For floor()

using namespace std;


class zSDF
{
public:
	zSpatialField() {};
	~zSpatialField() {};

	vector<float> minBB;
	vector<float> maxBB;
	int num_X;
	int num_Y;
	int num_Z;

	vector<vector<float>> positions;
	vector<int> values;

	// Create function to initialize the spatial field
	void create(const vector<float>& _minBB, const vector<float>& _maxBB, int _num_X, int _num_Y, int _num_Z)
	{
		minBB = _minBB;
		maxBB = _maxBB;
		num_X = _num_X;
		num_Y = _num_Y;
		num_Z = _num_Z;

		int num = num_X * num_Y * num_Z;
		positions.reserve(num);
		values.resize(num, -1);  // Initialize values to -1

		float uX = (maxBB[0] - minBB[0]) / (double)(num_X - 1);
		float uY = (maxBB[1] - minBB[1]) / (double)(num_Y - 1);
		float uZ = (maxBB[2] - minBB[2]) / (double)(num_Z - 1);

		// Generate voxel positions
		for (size_t i = 0; i < num_Z; i++)
		{
			for (size_t j = 0; j < num_Y; j++)
			{
				for (size_t k = 0; k < num_X; k++)
				{
					positions.push_back({
						minBB[0] + k * uX,
						minBB[1] + j * uY,
						minBB[2] + i * uZ
					});
				}
			}
		}
	}

	// Function to compute voxel index from 3D coordinates
	int getIndex(int x, int y, int z) const
	{
		if (x < 0 || x >= num_X || y < 0 || y >= num_Y || z < 0 || z >= num_Z)
			return -1; // Out of bounds
		return z * (num_X * num_Y) + y * num_X + x;
	}

	// Set value at a specific position
	void setValue(const vector<float>& pos, int value)
	{
		int x = floor((pos[0] - minBB[0]) / (maxBB[0] - minBB[0]) * (num_X - 1));
		int y = floor((pos[1] - minBB[1]) / (maxBB[1] - minBB[1]) * (num_Y - 1));
		int z = floor((pos[2] - minBB[2]) / (maxBB[2] - minBB[2]) * (num_Z - 1));

		int idx = getIndex(x, y, z);
		if (idx != -1)
			values[idx] = value;
	}

	// Get value at a specific position
	int getValue(const vector<float>& pos) const
	{
		int x = floor((pos[0] - minBB[0]) / (maxBB[0] - minBB[0]) * (num_X - 1));
		int y = floor((pos[1] - minBB[1]) / (maxBB[1] - minBB[1]) * (num_Y - 1));
		int z = floor((pos[2] - minBB[2]) / (maxBB[2] - minBB[2]) * (num_Z - 1));

		int idx = getIndex(x, y, z);
		return (idx != -1) ? values[idx] : -1; // Return -1 if out of bounds
	}
};

