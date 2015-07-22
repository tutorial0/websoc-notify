var app = angular.module("app", ["xeditable", "ngTagsInput"]);


app.run(function(editableOptions) {
    editableOptions.theme = 'bs3'; // bootstrap3 theme. Can be also 'bs2', 'default'
});


app.controller('Ctrl', ['$scope', '$http', function($scope, $http) {
    function bindWatch(index) {
        $scope.$watch('data['+index+']["_courses"].length', function(v) {
            $scope.newData[index]['_courses'] = $scope.data[index]['_courses'].map(function(item) { return parseInt(item.text) || item; });
        });
    }

    $scope.sortOrder = ['_user', '_email', '_courses'];

    $http.get('/user_data')
    .then(function(res){
        $scope.data = res.data;
        $scope.newData = angular.copy(res.data);
    }).then( function(){
        angular.forEach($scope.data, function(value, i) {
            bindWatch(i);
        });
    });

    $scope.removeUser = function(index) {
        delete $scope.newData[index]
        delete $scope.data[index]
    };

    $scope.addUser = function() {
        var keys = Object.keys($scope.data)
        var newKey = parseInt(keys[keys.length-1])+1;
        $scope.data[newKey] = {
            '_user': Math.random().toString(36).substring(7),
            '_email': '',
            '_courses': []
        };

        bindWatch(newKey);

        $scope.newData[newKey] = angular.copy($scope.data[newKey]);
    };

    $scope.submit = function() {
        $http.put('/user_data', $scope.newData)
    };
}]);
