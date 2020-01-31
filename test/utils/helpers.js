const testWillThrow = async (contractFunction, input, args, errorMessage) => {
	try {
		await contractFunction(...input, args)

		assert(false, 'contract failed to throw an error')
	} catch (error) {
		assert(
			RegExp(errorMessage).test(error),
			`the error message => ${errorMessage} => does not match => ${error}`
		)
	}
}

module.exports = { testWillThrow } 